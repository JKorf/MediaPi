from threading import Lock

from Shared.LogObject import LogObject
from Shared.Util import current_time


class AverageCounter(LogObject):

    @property
    def value(self):
        with self.item_lock:
            self.items = [x for x in self.items if current_time() - x[0] < self._retaining]
            self.last_result = sum([x[1] for x in self.items]) // self.seconds_average
            return self.last_result

    def get_speed(self):
        return sum([x[1] for x in self.items if current_time() - x[0] < 1000])

    def __init__(self, parent, seconds_average):
        super().__init__(parent, "speed")
        self.items = []
        self.seconds_average = seconds_average
        self._retaining = seconds_average * 1000
        self.item_lock = Lock()
        self.total = 0
        self.last_result = 0

    def add_value(self, value):
        with self.item_lock:
            self.items.append((current_time(), value))
            self.items = [x for x in self.items if current_time() - x[0] < self._retaining]
        self.total += value