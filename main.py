#reads the video and runs the detect
#counters on the top left corner.
#summary table is printed when the program finishes

import argparse
import os
import time
import cv2
from detector import VehicleDetector, box_to_centroid
from tracker import CentroidTracker
from counter import LineCounter

#bgr
COLOR_BOX = (0, 255, 0)
COLOR_LINE = (0, 0, 255)
COLOR_TEXT = (255, 255, 255)
COLOR_CENTROID = (0, 165, 255)
#output file
OUTPUT_VIDEO_DIR = os.path.join("output", "video")
OUTPUT_IMAGE_DIR = os.path.join("output", "image")

#file path
def build_output_path(filename, directory):

    if os.path.dirname(filename):
        target = filename
    else:
        target = os.path.join(directory, filename)

    parent = os.path.dirname(target)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return target

def parse_args():
    parser = argparse.ArgumentParser(description="YOLO based vehicle counting system")
    parser.add_argument("--video", required=True)
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.4)
    #counting line position, 0.0 = top, 1.0 = bottom             #0.6 was chosen experimentally
    parser.add_argument("--line", type=float, default=0.6)
    parser.add_argument("--output", default=None)
    #save every Nth frame for the report figures, 0 = off
    parser.add_argument("--save-frames", type=int, default=0)
    parser.add_argument("--no-show", action="store_true")
    #start and max frames for input
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--max-frames", type=int, default=None)
    return parser.parse_args()

def main():
    args = parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"ERROR: could not open video -> {args.video}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_video = cap.get(cv2.CAP_PROP_FPS) or 25

    #skip to the requested frame (for processing a section)
    if args.start_frame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)

    #y coordinate of the counting line
    line_y = int(height * args.line)
    detector = VehicleDetector(model_path=args.model, conf_threshold=args.conf)
    tracker = CentroidTracker(max_distance=60, max_disappeared=15)
    counter = LineCounter(line_y=line_y)



    #video recording
    writer = None
    output_path = None
    if args.output:
        output_path = build_output_path(args.output, OUTPUT_VIDEO_DIR)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps_video, (width, height))

    #frame recording
    if args.save_frames > 0:
        os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)
    saved_frame_count = 0


    #detections in every frame
    naive_count = 0
    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break  #end of video
        #max frame limit
        if args.max_frames is not None and frame_count >= args.max_frames:
            break
        frame_count += 1

        #information during proccess
        if frame_count % 100 == 0:
            print(f"  {frame_count} frames processed, current count: {counter.total}")

        #DETECTION
        boxes = detector.detect(frame)
        naive_count += len(boxes)

        #TRACKING
        centroids = [box_to_centroid(b) for b in boxes]
        class_names = [b[4] for b in boxes]
        objects = tracker.update(centroids, class_names)

        #COUNTING
        #most votes for id
        object_labels = {oid: tracker.get_label(oid) for oid in objects}
        counter.update(objects, object_labels)

        #DRAWING
        #red line
        cv2.line(frame, (0, line_y), (width, line_y), COLOR_LINE, 2)

        #boxes and names
        for (x1, y1, x2, y2, label) in boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_BOX, 2)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_BOX, 1)

        #ids, center point and the class by voting
        for object_id, (cx, cy) in objects.items():
            cv2.circle(frame, (cx, cy), 4, COLOR_CENTROID, -1)
            cv2.putText(frame, f"ID {object_id} {object_labels[object_id]}", (cx - 25, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_CENTROID, 2)

        #counter panel
        box_height = 100 + 22 * len(counter.count_by_class)
        cv2.rectangle(frame, (10, 10), (260, box_height), (0, 0, 0), -1)
        cv2.putText(frame, f"Down: {counter.count_down}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_TEXT, 2)
        cv2.putText(frame, f"Up: {counter.count_up}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_TEXT, 2)
        cv2.putText(frame, f"TOTAL: {counter.total}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_TEXT, 2)

        #class list under the total
        text_y = 90
        for name, amount in sorted(counter.count_by_class.items(), key=lambda x: -x[1]):
            text_y += 22
            cv2.putText(frame, f"  {name}: {amount}", (20, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_TEXT, 1)

        if writer is not None:
            writer.write(frame)

        #sample frames
        if args.save_frames > 0 and frame_count % args.save_frames == 0:
            image_name = f"frame_{args.start_frame + frame_count:06d}.jpg"
            cv2.imwrite(os.path.join(OUTPUT_IMAGE_DIR, image_name), frame)
            saved_frame_count += 1

        if not args.no_show:
            cv2.imshow("Vehicle Counting System", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    elapsed = time.time() - start_time
    fps_processing = frame_count / elapsed if elapsed > 0 else 0

    cap.release()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()

    #summary table
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Model                  : {args.model}")
    print(f"Frames processed       : {frame_count}")
    print(f"Processing speed (FPS) : {fps_processing:.2f}")
    print("-" * 50)
    print(f"Going down             : {counter.count_down}")
    print(f"Going up               : {counter.count_up}")
    print(f"TRACKED COUNT (ours)   : {counter.total}")
    print(f"NAIVE COUNT (baseline) : {naive_count}")
    print("-" * 50)
    print("CLASS BREAKDOWN")

    if counter.count_by_class:
        # sort from the most to least
        for name, amount in sorted(counter.count_by_class.items(), key=lambda x: -x[1]):
            ratio = 100 * amount / counter.total if counter.total else 0
            print(f"  {name:12s}: {amount:4d}  ({ratio:.1f}%)")
    else:
        print("  (no vehicle crossed the line)")
    print("=" * 50)



    #outputs
    if output_path or saved_frame_count:
        print("-" * 50)

        if output_path:
            print(f"Video saved            : {output_path}")

        if saved_frame_count:
            print(f"Frames saved           : {saved_frame_count} -> {OUTPUT_IMAGE_DIR}")

if __name__ == "__main__":
    main()


        
