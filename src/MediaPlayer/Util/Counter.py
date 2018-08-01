from threading import Lock

from Shared.Util import current_time


class Counter:

    def __init__(self):
        self.last_seconds = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
        self.loop_number = 0
        self.current_counter_value = 0
        self.total = 0
        self.last_update = current_time()
        self.last_result_time = 0
        self.last_result = 0
        self.max = 0
        self.__lock = Lock()

    @property
    def value(self):
        if current_time() - self.last_result_time < 500:
            return self.last_result

        total_time = 0
        total_value = 0
        for time, value in self.last_seconds:
            total_time += time
            total_value += value
        if total_time == 0:
            total_time = 1

        self.last_result_time = current_time()
        self.last_result = total_value / (total_time / 1000)

        if self.last_result > self.max:
            self.max = self.last_result

        return self.last_result

    def add_value(self, val):
        with self.__lock:
            self.current_counter_value += val
            self.total += val

    def update(self):
        with self.__lock:
            self.last_seconds[self.loop_number] = (current_time() - self.last_update, self.current_counter_value)
            self.last_update = current_time()

            self.current_counter_value = 0

        self.loop_number += 1
        if self.loop_number == 5:
            self.loop_number = 0
        return True
