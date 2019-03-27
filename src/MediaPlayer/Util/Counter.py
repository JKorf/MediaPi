from threading import Lock

from Shared.LogObject import LogObject
from Shared.Util import current_time


class AverageCounter(LogObject):

    @property
    def value(self):
        self.items = [x for x in self.items if current_time() - x[0] < self._retaining]
        last_result = sum([x[1] for x in self.items]) // self.seconds_average
        self.parent.speed_log = last_result
        return last_result

    def get_speed(self):
        return sum([x[1] for x in self.items if current_time() - x[0] < 1000])

    def __init__(self, parent, seconds_average):
        super().__init__(parent, "counter")
        self.parent = parent
        self.items = []
        self.seconds_average = seconds_average
        self._retaining = seconds_average * 1000
        self.total = 0

    def add_value(self, value):
        self.items.append((current_time(), value))
        self.items = [x for x in self.items if current_time() - x[0] < self._retaining]
        self.total += value
