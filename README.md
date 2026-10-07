# Real-Time Vehicle Counting System Using YOLO

A course project for Introduction to Computer Vision (CMP 3011). The system
detects vehicles in traffic videos with YOLOv8, tracks them with our own
centroid tracker, and counts the vehicles that cross a virtual line.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Input videos are kept in the `input/` directory and the path is given in full:

```bash
python main.py --video input/example.mp4
```

To save the result video:

```bash
python main.py --video input/example.mp4 --output example_result.mp4
```

To save sample frames for the report (every 100th frame):

```bash
python main.py --video input/example.mp4 --output example_result.mp4 --save-frames 100
```

To run with a different model:

```bash
python main.py --video input/example.mp4 --model yolov8s.pt
```
```bash
python main.py --video input/example.mp4 --model yolov8m.pt
```

To estimate the average speed of the traffic:

```bash
python speed.py --video input/example.mp4
```

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `--video` | (required) | Input video file (e.g. `input/example.mp4`) |
| `--model` | `yolov8n.pt` | YOLO model file (`n`, `s`, `m`) |
| `--conf` | `0.4` | Detection confidence threshold |
| `--line` | `0.6` | Vertical position of the counting line (0.0 top, 1.0 bottom) |
| `--output` | none | Name of the result video (saved under `output/video/`) |
| `--save-frames` | `0` | Save every Nth frame under `output/image/` |
| `--start-frame` | `0` | Start processing from this frame |
| `--max-frames` | none | Process at most this many frames |
| `--no-show` | off | Run without opening a window |

## Project Structure

| File | Purpose |
|---|---|
| `detector.py` | Vehicle detection with YOLOv8 (COCO classes: car, motorcycle, bus, truck) |
| `tracker.py` | Centroid based object tracking - matching by euclidean distance |
| `counter.py` | Counting by line crossing, every ID is counted once |
| `main.py` | Main loop, drawing and the summary table |
| `speed.py` | Speed estimation experiment (separate from the counting system) |

Directories:

```
input/       # source videos
docs/        # report sections
output/
├── video/   # processed result videos
└── image/   # sample frames
```

## Dataset

The test video is a publicly available traffic recording:

K. Majek, "4K Road traffic video for object detection and tracking - free
download now!", YouTube, 16 July 2018. https://youtu.be/MNn9qKG2UFI

Licensed under Creative Commons Attribution (CC BY). A two minute section was
cut from the original recording and is used as `input/trafic_sample_2_min.mp4`.

## Evaluation

For the accuracy measurement the vehicles in the test video are counted by hand
and the following formula is used:

```
Accuracy = 1 - |prediction - ground truth| / ground truth
```

Measured results are given in `docs/results_report.md`.

## Known Limitations

- When vehicles occlude each other the track ID may change, which leads to
  missed counts.
- Detection performance drops in night footage and in heavy traffic.
- The line position must be tuned per video with `--line`. Close to the camera
  vehicles move a large number of pixels between frames, so a crossing can be
  missed.
- The total vehicle count is reliable, but the class breakdown is sensitive to
  the choice of detector; some passenger cars are labelled as buses.
- Motorcycles are not counted. `motorcycle` is one of the accepted classes, but
  in the test video the detector never scores a motorcycle above 0.34, which is
  below the 0.4 confidence threshold. Lowering the threshold does not help: it
  still counts no motorcycle and inflates the total count from 125 to 151.
  See section 6.7 of `docs/results_report.md` for the full analysis.
- `speed.py` reports the average speed of the traffic, not the speed of a single
  vehicle. Two variants of the method agree with an independent estimate for the
  flow as a whole (40-50 km/h against 31-41 km/h) but can differ by a factor of
  two for one vehicle, because the estimated distance is very sensitive to the
  measured box width when the vehicle is far away. The camera focal length is
  also assumed rather than known. See section 6.8 of `docs/results_report.md`.

## License

The source code is released under the MIT License (see `LICENSE`). The test
video is the property of its author and is used under its own Creative Commons
Attribution licence (see the Dataset section above).

## Acknowledgments

This project was developed as the final term project for the CMP 3011
(Introduction to Computer Vision) course.
