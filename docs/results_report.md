# 6. Experimental Results

> This file has been prepared for the Experimental Results section of the
> report. All numbers were obtained from actual runs.

## 6.1 Experimental Setup

| Component | Value |
|---|---|
| CPU | AMD Ryzen 5 7500F (6 cores / 12 threads) |
| RAM | 32 GB |
| GPU | Not used (CPU build of PyTorch) |
| Python | 3.13.7 |
| PyTorch | 2.13.0+cpu |
| Ultralytics | 8.4.101 |
| OpenCV | 5.0.0 |

The system was executed on the CPU only, without a discrete GPU.

## 6.2 Test Data and Ground Truth

| Property | Value |
|---|---|
| Video | `trafic_sample_2_min.mp4` |
| Resolution | 1280 x 720 |
| Frame rate | 30 FPS |
| Total duration | 120.6 seconds (3619 frames) |

The system was evaluated at two different scales: a short section of 30 seconds
and the full video of 2 minutes.

| Evaluation set | Frames | Duration | Ground truth |
|---|---|---|---|
| Short section | First 900 | 30 s | 31 vehicles |
| Full video | 3619 | 120.6 s | 124-125 vehicles |

**Ground truth:** Both sets were watched and counted manually. In every case all
vehicles travel downwards (towards the camera); there are no crossings in the
reverse direction.

For the short section the manual count is unambiguous (31 vehicles). Two
different positions of the counting line (50% and 60% of the frame height) were
counted separately, and the ground truth was confirmed to be 31 at both
positions.

For the full video the manual count could not be determined with single vehicle
precision; the observer reported 124 or 125 vehicles with a possible miss of one
vehicle. The results below are therefore given for both values. This uncertainty
of roughly 1% is of the same order as the error of the system itself, and it
does not change the ranking of the models.

## 6.3 Effect of the Counting Line Position

The vertical position of the counting line is the only free design parameter of
the system. Four positions were tested with the YOLOv8n model in order to
measure the effect of this parameter.

| Line position | Down | Up | Total | Note |
|---|---|---|---|---|
| 0.50 | 30 | 1 | 31 | Produces a false reverse crossing |
| 0.55 | 33 | 0 | 33 | Count inflates (identity switches) |
| **0.60** | **30** | **0** | **30** | **Selected value** |
| 0.65 | 30 | 0 | 30 | Vehicles may leave the frame before crossing |

Findings:

- **At 0.50** the system produces a reverse crossing that does not exist in
  reality. Although the total count of 31 is equal to the ground truth, this
  result consists of two errors that cancel each other out: one vehicle
  travelling downwards was missed, and one false reverse crossing was counted.
- **At 0.55** the count rises to 33. In this region vehicles partially occlude
  each other and identity switches occur during tracking.
- **At 0.60** the reverse direction error disappears and the system makes a
  single missed-count error.
- **At 0.65** vehicles get very close to the camera and, because the road curves
  to the left, some of them leave the frame before crossing the line.

For this reason the line position was set to **0.60** for the rest of the study.
The results for the 0.50 position are also reported for comparison.

## 6.4 Model Comparison

Three YOLOv8 model sizes were tested with identical tracking parameters
(`max_distance = 60`, `max_disappeared = 15`, `conf = 0.4`) and the selected
line position (0.60).

### Full video, 3619 frames (main result)

| Model | FPS | Down | Up | Count | Accuracy (GT 124) | Accuracy (GT 125) |
|---|---|---|---|---|---|---|
| **YOLOv8n** | **33.68** | 125 | 0 | **125** | **99.2%** | **100.0%** |
| YOLOv8s | 18.72 | 135 | 0 | 135 | 91.1% | 92.0% |
| YOLOv8m | 8.64 | 139 | 0 | 139 | 87.9% | 88.8% |

The ordering of the models is identical for both ground truth values, and the
difference between the two columns stays below one percentage point. The
uncertainty of the manual count therefore does not affect the conclusion.

None of the three models reported a crossing in the reverse direction, which is
consistent with the ground truth.

### Cost of video recording

Writing the annotated result video to disk was measured separately with YOLOv8n
on the full video:

| Configuration | FPS | Count |
|---|---|---|
| Without recording | 33.68 | 125 |
| With recording | 29.66 | 125 |

Recording costs approximately 12% of the processing speed but has no effect on
the counting result. The speed values reported elsewhere in this section were
measured without recording.

### Short section, 900 frames

The same comparison on the 30 second section, used for the line position study:

#### Line position 0.60 (selected configuration)

| Model | FPS | Down | Up | Count | Error | Accuracy |
|---|---|---|---|---|---|---|
| **YOLOv8n** | **32.45** | 30 | 0 | 30 | −1 | **96.8%** |
| YOLOv8s | 17.70 | 32 | 0 | 32 | +1 | 96.8% |
| YOLOv8m | 8.28 | 35 | 0 | 35 | +4 | 87.1% |

#### Line position 0.50 (comparison)

| Model | FPS | Down | Up | Count | Error | Accuracy |
|---|---|---|---|---|---|---|
| YOLOv8n | 32.22 | 30 | 1 | 31 | 0 | 100.0% |
| YOLOv8s | 17.12 | 33 | 0 | 33 | +2 | 93.5% |
| YOLOv8m | 8.22 | 34 | 0 | 34 | +3 | 90.3% |

Accuracy was computed with the following formula:

```
Accuracy = 1 - |prediction - ground truth| / ground truth
```

### Precision, recall and F1

The counting accuracy defined above compares two totals and cannot distinguish
between a missed vehicle and a vehicle that was counted twice. A count of 30
against a ground truth of 31 may mean one missed vehicle, or one false count
together with two missed vehicles. These cases have the same accuracy but very
different behaviour, so the individual counting events were verified manually.

Every crossing event produced by YOLOv8n on the 900 frame section was logged
with its frame number, track identity, horizontal position and assigned class.
Events that were close to each other in time and position were treated as
candidates for double counting and the corresponding frames were inspected
visually. Four such candidate pairs were found, together with the single truck
crossing. The inspection showed that in each case two distinct vehicles were
involved, crossing the line either one after another in the same lane or side
by side in different lanes. No event corresponded to the same vehicle being
counted twice.

| Quantity | Value |
|---|---|
| True positives (correctly counted vehicles) | 30 |
| False positives (counts without a vehicle) | 0 |
| False negatives (vehicles not counted) | 1 |

| Metric | Value |
|---|---|
| Precision | 1.000 |
| Recall | 0.968 |
| F1 score | 0.984 |

```
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 * Precision * Recall / (Precision + Recall)
```

A precision of 1.000 means that every vehicle reported by the system is a real
vehicle: the system never invents a crossing. Its only error is a missed
vehicle, which is reflected in the recall of 0.968.

This behaviour is desirable for a traffic counting application, because the
reported number is a lower bound on the real traffic volume rather than an
inflated figure. It is also consistent with the model comparison above: the
larger models produced counts of 32 and 35 against the same ground truth of 31,
so their additional detections necessarily introduce false positives and their
precision is lower.

These values were obtained for YOLOv8n at line position 0.60 on the 900 frame
section. The same verification was not carried out for YOLOv8s and YOLOv8m, so
precision and recall are not reported for those models.

### Discussion

On the full video YOLOv8n is both the fastest and the most accurate model. The
gap between the models widens with the length of the evaluation: on the 30
second section the three models produced 30, 32 and 35 vehicles, while on the
full video they produced 125, 135 and 139. The over-counting of the larger
models is therefore systematic rather than incidental.

On the short section at the 0.60 position YOLOv8n and YOLOv8s reach the same
accuracy (96.8%), but YOLOv8n runs approximately twice as fast (32.45 FPS vs
17.70 FPS). On the full video YOLOv8n is clearly ahead of both larger models.

At the 0.50 position the 100% result of YOLOv8n originates from two errors that
cancel each other out, as explained above. Therefore, despite the higher
accuracy figure, the 0.50 configuration reflects the true performance of the
system less reliably.

## 6.5 Comparison with the Baseline

In order to measure the contribution of the tracking stage, a naive method that
does not use object tracking was implemented. This method adds up the number of
vehicles detected in every frame.

On the full video:

| Method | Count | Ground truth | Deviation |
|---|---|---|---|
| Naive count (no tracking) | 27810 | 124-125 | 223x too high |
| Proposed method (YOLOv8n + tracking) | 125 | 124-125 | 0-1 vehicle |

On the 30 second section:

| Method | Count | Ground truth | Deviation |
|---|---|---|---|
| Naive count (no tracking) | 6569 | 31 | 212x too high |
| Proposed method (YOLOv8n + tracking) | 30 | 31 | 1 vehicle |

Because the naive method counts the same vehicle again in every frame in which
it appears, it does not produce a usable result. This comparison shows that
centroid based tracking together with identity based unique counting is
essential for the accuracy of the system.

The naive count is independent of the line position (6569 at both positions),
because this method does not use line crossing at all.

## 6.6 Class Breakdown

Full video, 0.60 line position:

| Model | Car | Bus | Truck | Total |
|---|---|---|---|---|
| YOLOv8n | 102 | 14 | 9 | 125 |
| YOLOv8s | 111 | 4 | 17 | 135 |
| YOLOv8m | 110 | 3 | 23 | 139 |

30 second section, 0.60 line position:

| Model | Car | Bus | Truck | Total |
|---|---|---|---|---|
| YOLOv8n | 26 | 3 | 1 | 30 |
| YOLOv8s | 28 | 1 | 3 | 32 |
| YOLOv8m | 28 | 0 | 7 | 35 |

While the three models produce comparable results for the total number of
vehicles, they differ clearly in the class distribution, and the disagreement is
much more visible on the full video. The number of buses falls from 14 to 4 and
3 as the model grows, while the number of trucks rises from 9 to 17 and 23. In
other words, most of the vehicles that YOLOv8n labels as buses are labelled as
trucks by YOLOv8m. Visual inspection showed that several of these vehicles are
in fact passenger cars and were misclassified.

This result shows that the **total vehicle count of the system is reliable**,
whereas the **class breakdown is sensitive to the choice of detector**.

## 6.7 Undetected Motorcycles

Although `motorcycle` is one of the four vehicle classes accepted by the system,
none of the model configurations counted a single motorcycle, even though
motorcycles are visible in the video. This case was investigated separately.

The video was scanned with a very low confidence threshold (0.05) and the raw
detections of every COCO class were collected:

| Class | Detections | Highest score |
|---|---|---|
| car | 1691 | 0.87 |
| bus | 353 | 0.86 |
| truck | 227 | 0.85 |
| motorcycle | 20 | **0.34** |

Motorcycles are therefore detected by the model, but with a confidence that never
exceeds 0.34, which is below the operating threshold of 0.40. Every motorcycle
detection is discarded before it reaches the tracking stage.

Lowering the threshold does not solve the problem. At `conf = 0.30` nine tracks
received the motorcycle label, yet none of them was counted, while the total
count rose from 125 to 151 against a ground truth of 124-125 (accuracy dropping
from 100% to approximately 79%). The additional low confidence detections create
spurious identities and inflate the count.

The reason no motorcycle is counted even when it is tracked was determined by
examining the vertical positions of the motorcycle tracks with respect to the
counting line (y = 432):

| Track | Frames | y range | Crosses the line |
|---|---|---|---|
| 196 | 1223-1245 | 373-387 | no (stays above) |
| 201 | 1249-1276 | 457-515 | no (stays below) |
| 204 | 1261-1309 | 523-680 | no (stays below) |
| 218 | 1298-1330 | 475-655 | no (stays below) |

Motorcycle detections are intermittent, so a track typically appears only after
the motorcycle has already passed the counting line. Track 201, for example, is
first seen at y = 457, which is already below the line; the condition "above the
line in the previous frame, below it in this frame" is therefore never satisfied.
Some of the remaining tracks are stationary (constant y), which correspond to
parked motorcycles that should not be counted at all.

All motorcycle tracks occur between frames 1223 and 1330, that is between roughly
the 41st and 44th second of the video, which matches the visual observation that
the motorcycles appear as a small group.

**Conclusion:** The motorcycle class is retained in the implementation because it
is conceptually part of the counting task, but under the current configuration
the system does not count motorcycles. This is a limitation of the detector on
small objects at this camera distance, not of the tracking or counting stages.

## 6.8 Speed Estimation

As an additional experiment, the average speed of the traffic was estimated from
the same detections. Two methods were implemented and compared (`speed.py`).

### Method A: lateral scale

A vehicle of known real width W seen as w pixels gives a scale of w/W pixels per
metre at that point of the image. The vertical displacement of the centroid is
divided by this scale to obtain the distance travelled. The scale is taken from
the vehicle itself, so it adapts to perspective automatically.

This method produced a median speed of **11.4 km/h**, which is far too low for an
urban road. The reason is conceptual: the box width provides a *lateral* scale
(left to right), whereas the vehicles move in *depth* (towards the camera).
These two directions do not have the same number of pixels per metre.

### Method B: distance from apparent size

A known real width W observed as w pixels places the vehicle at a distance

```
Z = f * W / w
```

where f is the focal length in pixels. The distance travelled between two
reference lines is then Z₁ − Z₂, and the speed follows from the elapsed time.
Because depth motion is measured with a depth scale, the axis problem of
Method A does not occur.

The focal length of the camera is unknown. A horizontal field of view of
approximately 60° was assumed, giving f = 1109 px for a 1280 px wide frame. The
estimated speed scales linearly with f.

### Corrections required by Method B

The first implementation of Method B produced a median of 50.4 km/h but also a
maximum of 150.1 km/h, which is not physically possible, and the estimated
length of the visible road was inconsistent with the measured travel times. A
single track was therefore examined frame by frame:

| Frame | cy | Box width | Estimated Z |
|---|---|---|---|
| 236 | 536 | 183 px | 10.9 m |
| 239 | 580 | 204 px | 9.8 m |
| 243 | 626 | 165 px | 12.1 m |
| 248 | 670 | 103 px | 19.4 m |

The vertical position keeps increasing, so the vehicle keeps approaching, yet
the estimated distance starts growing again. The cause is that the bounding box
is **clipped** when the vehicle leaves the bottom of the frame: only part of the
vehicle remains visible, the measured width shrinks, and the vehicle appears to
move away. A second problem was detection noise; the width of one vehicle jumped
from 114 px to 165 px between two consecutive frames.

Two corrections were applied:

1. Boxes touching the frame border are discarded (434 detections in 900 frames).
2. The box width is median filtered over five frames.

After these corrections the impossible values disappeared (maximum 85.6 km/h)
and the measured track lengths became 40-69 m, which agrees with an independent
estimate of the length of the visible road.

### Results and validation

An independent estimate was used as a reference. Vehicles need about 7 seconds
to cross the frame; if the visible road is 60-80 m long this corresponds to
31-41 km/h.

| Method | Median speed |
|---|---|
| Method A (lateral scale) | 11.4 km/h |
| Method B (reference lines) | 50.4 km/h |
| Method B (whole track) | 39.0 km/h |
| **Independent estimate** | **31-41 km/h** |

Both variants of Method B are consistent with the independent estimate at the
level of the traffic flow, whereas Method A is approximately three times too
low, as predicted by its conceptual weakness.

However, the two variants of Method B do **not** agree for individual vehicles.
For one vehicle they produced 50.4 and 22.5 km/h, and disagreements of a factor
of two are common. The reason is the sensitivity of Z = f·W/w to the measured
width: for a distant vehicle, an error of one pixel in the box width corresponds
to approximately one metre of distance error.

**Conclusion:** The method is reported as an estimate of the **average speed of
the traffic** (roughly 40-50 km/h for this recording) and not as a per-vehicle
measurement. A metrically correct solution would require a homography
(bird's eye transformation) computed from four reference points measured on the
road surface, which is left as future work.

## 6.9 Speed / Accuracy Trade-off

As the models get larger, the number of detections per frame increases (naive
count on the full video: 27810 → 36553 → 38387). However, this increase affected
the counting accuracy negatively rather than positively: YOLOv8s counted 10 and
YOLOv8m counted 14 vehicles too many.

The reason is that larger models also detect distant and partially visible
vehicles in the background. These detections create additional identities during
tracking, and some of them cause false crossings around the counting line.

Since the video runs at 30 FPS, real-time operation requires a processing speed
of at least 30 FPS. Only YOLOv8n (33.68 FPS without recording, 29.66 FPS while
writing the result video) is close to or above this threshold; YOLOv8s and
YOLOv8m remain well below it.

**Conclusion:** YOLOv8n was selected for this application because it is the only
model that satisfies the real-time constraint and because it also produces the
most accurate count (125 vehicles against a ground truth of 124-125). Using
larger models increases the computational cost while reducing the counting
accuracy, and therefore provides no benefit in this scenario.
