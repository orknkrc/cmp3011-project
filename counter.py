#vehicle counting with a line crossing. if vehicles center point was above the line it is counted going down
#every id counting once. this prevent the false counts
#class of vehicle is also recorded wwhile counting

from collections import defaultdict

class LineCounter:
    def __init__(self, line_y):
        self.line_y = line_y
        self.previous_y = {}   # id   y value in the previous frame
        self.counted = set()   # ids that have already counted
        self.count_down = 0
        self.count_up = 0
        self.count_by_class = defaultdict(int)  # "car" -> 47

    def update(self, objects, labels=None):
        for object_id, (cx, cy) in objects.items():
            prev_y = self.previous_y.get(object_id)
            self.previous_y[object_id] = cy

            #first time we see this vehicle, no previous position to compare
            if prev_y is None:
                continue
            #this vehicle was already counted dont count it again
            if object_id in self.counted:
                continue
            #crossing from top to bottom
            if prev_y < self.line_y <= cy:
                self.count_down += 1
                self.counted.add(object_id)
            #crossing from bottom to top
            elif prev_y > self.line_y >= cy:
                self.count_up += 1
                self.counted.add(object_id)
            else:
                continue  #no crossing

            #crossing happenedadd the vehicles class to breakdown
            if labels is not None:
                self.count_by_class[labels.get(object_id, "unknown")] += 1

    @property
    def total(self):
        return self.count_down + self.count_up
