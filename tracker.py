#centroid based object tracking
#1. take the centre points of the vehicles detected in each frame
#2. compare these centres with the centres from the previous frame
#3. the closest pair is the same vehicle, it keeps the same id
#4. unmatched new centre, a new vehicle and it gets a new id
#5. id that has not seen for several frames, removed
#euclidean distance with start from the closest(greedy)

from collections import Counter, defaultdict
import numpy as np

class CentroidTracker:
    def __init__(self, max_distance=60, max_disappeared=15): #max_distance 60 if two centres are further apart than this many pixels they are not considered the same vehicle
                                                             #max_disappeared 15 how many frames a vehicle may be missing before it is removed
        self.next_id = 0
        self.objects = {}        #id  (cx, cy)
        self.disappeared = {}    #id  for how many frames it has been missing
        self.label_votes = defaultdict(Counter)  #id car 12, truck 1
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared

    #new vehicle
    def _register(self, centroid, label=None):
        self.objects[self.next_id] = centroid
        self.disappeared[self.next_id] = 0
        if label is not None:
            self.label_votes[self.next_id][label] += 1
        self.next_id += 1
    #remove
    def _deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]
    #class of vehicle
    def get_label(self, object_id):
        votes = self.label_votes.get(object_id)
        if not votes:
            return "unknown"
        return votes.most_common(1)[0][0]

    def update(self, centroids, labels=None): #centroids= list of centres detected, labels = class names
        if labels is None:
            labels = [None] * len(centroids)

        #no vehicles in this frame, increase the miss
        if len(centroids) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister(object_id)
            return self.objects

        #nothing is being tracked yet, register new
        if len(self.objects) == 0:
            for centroid, label in zip(centroids, labels):
                self._register(centroid, label)
            return self.objects

        #normal
        object_ids = list(self.objects.keys())
        object_centroids = np.array([self.objects[i] for i in object_ids])
        input_centroids = np.array(centroids)

        #distance matrix fpr tracked vehicle i and j(new)
        D = np.linalg.norm(
            object_centroids[:, None] - input_centroids[None, :], axis=2
        )

        used_rows = set()
        used_cols = set()

        #sort all distances ascending and start from the closest pair if a vehicle is matched it cannot be reused
        sorted_indices = np.unravel_index(np.argsort(D, axis=None), D.shape)
        for row, col in zip(*sorted_indices):
            if row in used_rows or col in used_cols:
                continue
            #too far, cannot vehicle
            if D[row, col] > self.max_distance:
                continue

            object_id = object_ids[row]
            self.objects[object_id] = (int(input_centroids[col][0]), int(input_centroids[col][1]))
            self.disappeared[object_id] = 0
            #add frames class prediction as a vote
            if labels[col] is not None:
                self.label_votes[object_id][labels[col]] += 1
            used_rows.add(row)
            used_cols.add(col)

        #unmatched tracked vehicles
        for row in range(D.shape[0]):
            if row in used_rows:
                continue
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self._deregister(object_id)

        #unmatched new detections
        for col in range(D.shape[1]):
            if col in used_cols:
                continue
            self._register((int(input_centroids[col][0]),
                            int(input_centroids[col][1])), labels[col])

        return self.objects