# 3. Dataset

> Section 3 of the report. The experimental measurements are in
> `results_report.md`.

## 3.1 Description of the Dataset

No dataset was collected or annotated for training in this project, because the
detection stage uses a YOLOv8 model that is already trained on the COCO dataset
[1]. The dataset of this study is therefore the video material on which the
system is evaluated.

A single publicly available traffic recording was used. The recording was made
from an elevated position overlooking an urban road with a junction. The camera
is stationary throughout, which is a requirement of the method: the counting
line is defined in image coordinates and would lose its meaning if the camera
moved.

The traffic in the recording flows in a single direction, towards the camera.
There are also parked vehicles on the left side of the road, which are visible
but never cross the counting line.

## 3.2 Source of the Dataset

| Property | Value |
|---|---|
| Title | 4K Road traffic video for object detection and tracking - free download now! |
| Author | Karol Majek |
| Platform | YouTube |
| Publication date | 16 July 2018 |
| URL | https://youtu.be/MNn9qKG2UFI |
| Licence | Creative Commons Attribution (CC BY) |

The recording is published under a Creative Commons Attribution licence, which
permits reuse provided that the author is credited. The author additionally
states in the video description that the video may be downloaded and used
freely. The attribution required by the licence is given here and in the
`README.md` file of the source code.

## 3.3 Video Properties

The original recording is longer than required for this study, so a two minute
section was cut from its beginning and used as the working file
(`input/trafic_sample_2_min.mp4`).

| Property | Value |
|---|---|
| Resolution | 1280 x 720 |
| Frame rate | 30 FPS |
| Duration | 120.6 seconds |
| Number of frames | 3619 |
| Colour format | RGB (read as BGR by OpenCV) |

Although the title of the original video states 4K, the copy obtained from the
platform is 1280 x 720. The resolution reported here is the resolution actually
processed by the system.

## 3.4 Ground Truth

The dataset contains no annotations, so the reference values used for the
evaluation were produced manually. The video was watched and the vehicles
crossing the counting line were counted by hand.

| Evaluation set | Frames | Duration | Ground truth |
|---|---|---|---|
| Short section | First 900 | 30 s | 31 vehicles |
| Full video | 3619 | 120.6 s | 124-125 vehicles |

For the short section the manual count is unambiguous. For the full video the
observer reported 124 or 125 vehicles, that is an uncertainty of one vehicle,
which is approximately 1% and is of the same order as the error of the system
itself. Both values are therefore carried through the evaluation in section 6.

Because the counting line is part of the definition of the task, the ground
truth depends on where the line is placed. The manual count was repeated for the
two line positions that are compared in section 6.3 (50% and 60% of the frame
height), and it was 31 vehicles in both cases for the short section.

## 3.5 Preprocessing

The system performs no preprocessing of its own. Frames are read with OpenCV and
passed directly to the model, which applies its own internal resizing and
normalisation. No filtering, background subtraction, colour conversion or
histogram operation is applied.

This is a deliberate choice. The detection stage is a pretrained convolutional
network that already expects raw camera images, and additional preprocessing
would move the input away from the distribution the model was trained on.

The only operations applied to the data are:

1. Cutting the two minute section from the original recording (done once,
   outside the program).
2. Selecting a frame range at run time with the `--start-frame` and
   `--max-frames` parameters, which is used to evaluate the short section
   without processing the whole video.

## References for this section

[1] T.-Y. Lin et al., "Microsoft COCO: Common Objects in Context," in *Proc.
    European Conf. Computer Vision (ECCV)*, 2014, pp. 740-755.

[2] K. Majek, "4K Road traffic video for object detection and tracking - free
    download now!," YouTube, 16 July 2018. [Online]. Available:
    https://youtu.be/MNn9qKG2UFI (Creative Commons Attribution licence).
