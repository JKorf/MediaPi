from threading import Lock, Event

import time

import itertools

from Shared.Logger import Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time


class AverageCounter:

    def __init__(self, name, seconds_average, caching_time):
        self.last_seconds = list(itertools.repeat(0, seconds_average))
        self.loop_number = 0
        self.current_counter_value = 0
        self.total = 0
        self.last_result_time = 0
        self.last_result = 0
        self.max = 0
        self.caching_time = caching_time
        self.name = name
        self.seconds_average = seconds_average
        self.thread = None
        self.running = False
        self.current_second = 0
        self.__lock = Lock()
        self.wait_event = Event()

    def start(self):
        self.running = True
        self.thread = CustomThread(self.update, self.name)
        self.thread.start()

    def stop(self):
        self.running = False
        self.wait_event.set()
        self.thread.join()

    @property
    def value(self):
        if current_time() - self.last_result_time < self.caching_time:
            return self.last_result

        self.last_result_time = current_time()
        self.last_result = sum(self.last_seconds) / self.seconds_average

        if self.last_result > self.max:
            self.max = self.last_result

        return self.last_result

    def add_value(self, val):
        with self.__lock:
            self.total += val
            self.current_second += val

    def update(self):
        while self.running:
            start_time = current_time()
            with self.__lock:
                self.loop_number += 1
                if self.loop_number == self.seconds_average:
                    self.loop_number = 0
                self.last_seconds[self.loop_number] = self.current_second
                self.current_second = 0

            self.wait_event.wait(max(1 - ((current_time() - start_time) / 1000), 0))


class LiveCounter:

    def __init__(self, name, update_time):
        self.data = []
        self.update_time = update_time
        self.name = name
        self.total = 0

        self.thread = None
        self.running = False
        self.__lock = Lock()

    def start(self):
        self.running = True
        self.thread = CustomThread(self.update, self.name)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    @property
    def value(self):
        return sum([v for t, v in self.data])

    def add_value(self, val):
        with self.__lock:
            self.data.append((current_time(), val))
            self.total += val

    def update(self):
        while self.running:
            start_time = current_time()
            with self.__lock:
                self.data = [x for x in self.data if current_time() - x[0] < 1000]
            time.sleep(max(self.update_time - (current_time() - start_time), 0) / 1000)
