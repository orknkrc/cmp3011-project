#speed estimation

#method a: naive, kept for comparison:
#  the box width gives pixels per metre at that point of the image, and the vertical pixel displacement is divided by it.
#  problem: the box width is a LATERAL scale (left to right) while the vehicles move in DEPTH (towards the camera). the two directions do not have the same pixels per metre, so this method underestimates the speed.

#method b: distance based, the one i use:
#a known real width W seen as w pixels means the vehicle is at distance
#      Z = f * W / w
#  where f is the focal length in pixels. the box gets wider as the vehicle approaches, so the change of Z between two reference lines is the real distance travelled, and speed = (Z1 - Z2) / time.
#  this measures depth motion with a depth scale, so the axis problem of first try

#two corrections to make this work:
#  1. boxes that touch the frame border are dropped. when a vehicle leaves the bottom of the frame its box gets clipped, the width shrinks and the vehicle looks like it is moving away again
#  2. the width is median smoothed over a few frames, a single frame can jump by 30-40% because of detection noise

#f is not known for this video. a horizontal field of view of like 60 degrees is assumed, which gives f = (width/2) / tan(30) = approx. 1100 px for a 1280 px frame the speed scales linearly with f

#so this file is used for the average speed of the traffic, not for the speed of an individual vehicle.


# TTHIS CODE IS NOT %100 CORRECT. IT JUST EXPERIMENTAL

import argparse
import statistics
from collections import defaultdict
import cv2
from detector import VehicleDetector, box_to_centroid
from tracker import CentroidTracker

#average real width in metres
VEHICLE_WIDTHS = {
    "car": 1.8,
    "bus": 2.55,
    "truck": 2.5,
    "motorcycle": 0.8,
}
DEFAULT_WIDTH = 1.8
BORDER_MARGIN = 4      #a box this close to the frame edge is treated as clipped
SMOOTH_WINDOW = 5      #median filter length for the box width

class SpeedEstimator:
    def __init__(self, fps, focal_px, ref_y1, ref_y2, step=10):
        self.fps = fps
        self.focal_px = focal_px
        self.ref_y1 = ref_y1      #upper reference line, vehicle is far
        self.ref_y2 = ref_y2      #lower reference line, vehicle is near
        self.step = step
        self.history = defaultdict(list)   #id -> [(frame, cy, width_px, label)]

    def update(self, object_id, frame_index, cy, box_width_px, label):
        if box_width_px <= 0:
            return
        self.history[object_id].append((frame_index, cy, box_width_px, label))

    def _real_width(self, label):
        return VEHICLE_WIDTHS.get(label, DEFAULT_WIDTH)

    def _distance_m(self, box_width_px, label):
        #Z = f * W / w
        return self.focal_px * self._real_width(label) / box_width_px

    #median filter, the raw width is too noisy to use directly
    def _smoothed_widths(self, history):
        widths = [w for _, _, w, _ in history]
        out = []
        half = SMOOTH_WINDOW // 2
        for i in range(len(widths)):
            lo = max(0, i - half)
            hi = min(len(widths), i + half + 1)
            out.append(statistics.median(widths[lo:hi]))
        return out

    #METHOD A
    def speed_naive(self, object_id):
        h = self.history[object_id]
        if len(h) < self.step + 1:
            return None
        speeds = []
        for i in range(len(h) - self.step):
            f1, y1, w1, label = h[i]
            f2, y2, w2, _ = h[i + self.step]
            dt = (f2 - f1) / self.fps
            ppm = ((w1 + w2) / 2) / self._real_width(label)
            if dt <= 0 or ppm <= 0:
                continue
            speeds.append(abs(y2 - y1) / ppm / dt * 3.6)
        if not speeds:
            return None
        speeds.sort()
        return speeds[len(speeds) // 2]

    #METHOD B
    def speed_reference_lines(self, object_id):
        h = self.history[object_id]
        if len(h) < SMOOTH_WINDOW:
            return None
        widths = self._smoothed_widths(h)

        #the sample where the vehicle passes each reference line
        first = None
        second = None
        for i, sample in enumerate(h):
            cy = sample[1]
            if first is None and cy >= self.ref_y1:
                first = (sample, widths[i])
            if first is not None and cy >= self.ref_y2:
                second = (sample, widths[i])
                break

        if first is None or second is None:
            return None

        (f1, _, _, label), w1 = first
        (f2, _, _, _), w2 = second
        dt = (f2 - f1) / self.fps
        if dt <= 0:
            return None

        #the vehicle approaches, so Z gets smaller
        distance_m = self._distance_m(w1, label) - self._distance_m(w2, label)
        if distance_m <= 0:
            return None
        return distance_m / dt * 3.6

    #how long is the visible road, used as a sanity check
    def road_length_m(self, object_id):
        h = self.history[object_id]
        if len(h) < SMOOTH_WINDOW:
            return None
        widths = self._smoothed_widths(h)
        label = h[0][3]
        return self._distance_m(widths[0], label) - self._distance_m(widths[-1], label)

def main():
    parser = argparse.ArgumentParser(description="speed estimation")
    parser.add_argument("--video", required=True)
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.4)
    parser.add_argument("--focal", type=float, default=1109.0)
    #reference lines as a fraction of the frame height
    parser.add_argument("--ref1", type=float, default=0.35)
    parser.add_argument("--ref2", type=float, default=0.75)
    parser.add_argument("--max-frames", type=int, default=None)
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"ERROR: could not open video -> {args.video}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    ref_y1 = int(height * args.ref1)
    ref_y2 = int(height * args.ref2)

    detector = VehicleDetector(model_path=args.model, conf_threshold=args.conf)
    tracker = CentroidTracker(max_distance=60, max_disappeared=15)
    estimator = SpeedEstimator(fps=fps, focal_px=args.focal,
                               ref_y1=ref_y1, ref_y2=ref_y2)

    frame_index = 0
    clipped = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if args.max_frames is not None and frame_index >= args.max_frames:
            break
        frame_index += 1

        boxes = detector.detect(frame)
        centroids = [box_to_centroid(b) for b in boxes]
        class_names = [b[4] for b in boxes]

        #centroid -> box width, clipped boxes are skipped
        width_of = {}
        for centroid, box in zip(centroids, boxes):
            x1, y1, x2, y2, _ = box
            if (x1 <= BORDER_MARGIN or y1 <= BORDER_MARGIN or
                    x2 >= width - BORDER_MARGIN or y2 >= height - BORDER_MARGIN):
                clipped += 1
                continue
            width_of[centroid] = x2 - x1

        objects = tracker.update(centroids, class_names)
        for object_id, centroid in objects.items():
            if centroid in width_of:
                estimator.update(object_id, frame_index, centroid[1],
                                 width_of[centroid], tracker.get_label(object_id))

    cap.release()

    rows = []
    lengths = []
    for object_id in estimator.history:
        b = estimator.speed_reference_lines(object_id)
        if b is None or b <= 1:
            continue
        a = estimator.speed_naive(object_id)
        rows.append((object_id, tracker.get_label(object_id), a, b))
        length = estimator.road_length_m(object_id)
        if length and length > 0:
            lengths.append(length)

    print("\n" + "=" * 58)
    print("SPEED ESTIMATION")
    print("=" * 58)
    print(f"Frames processed    : {frame_index}")
    print(f"Assumed focal length: {args.focal:.0f} px")
    print(f"Reference lines     : y = {ref_y1} and y = {ref_y2}")
    print(f"Clipped boxes drop  : {clipped}")
    print(f"Vehicles measured   : {len(rows)}")
    print("-" * 58)

    if not rows:
        print("no vehicle could be measured")
        return

    b_speeds = sorted(r[3] for r in rows)
    a_speeds = sorted(r[2] for r in rows if r[2] is not None)
    n = len(b_speeds)

    print("METHOD B (reference lines + distance)")
    print(f"  minimum : {b_speeds[0]:.1f} km/h")
    print(f"  median  : {b_speeds[n // 2]:.1f} km/h")
    print(f"  maximum : {b_speeds[-1]:.1f} km/h")
    if a_speeds:
        m = len(a_speeds)
        print("METHOD A (naive, lateral scale)")
        print(f"  median  : {a_speeds[m // 2]:.1f} km/h")
    if lengths:
        lengths.sort()
        print(f"Estimated visible road length: {lengths[len(lengths) // 2]:.0f} m")
    print("-" * 58)
    print(f"{'ID':>5}  {'class':10}  {'method A':>10}  {'method B':>10}")
    for object_id, label, a, b in rows[:15]:
        a_text = f"{a:.1f}" if a is not None else "-"
        print(f"{object_id:5d}  {label:10}  {a_text:>10}  {b:10.1f}")
    print("=" * 58)

if __name__ == "__main__":
    main()
