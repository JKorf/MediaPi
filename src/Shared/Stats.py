from threading import Lock

import time

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Observable import Observable
from Shared.Threading import CustomThread
from Shared.Util import Singleton


class StatList(Observable):

    def __init__(self):
        super().__init__("Stats", 1)
        self.statistics = dict()

    def update(self, name, value):
        self.statistics[name] = value
        self.changed()

    def get(self, name):
        if name in self.statistics:
            return float(self.statistics[name])
        return 0


class Stats(metaclass=Singleton):

    cache = StatList()

    def __init__(self):
        self.changed = False
        self.work_thread = CustomThread(self.save_stats, "Stat saver", [])

    def start(self):
        stats = Database().get_stats()
        for key, value, last_change in stats:
            self.cache.update(key, value)

        self.work_thread.start()

    def _update_stat(self, name, value):
        self.cache.update(name, value)
        self.changed = True

    def save_stats(self):
        while True:
            if self.changed:
                self.changed = False
                copy = self.cache.statistics.copy()
                Logger().write(LogVerbosity.Debug, "Saving stats")
                for key, val in copy.items():
                    Database().update_stat(key, val)

            time.sleep(15)

    def add(self, name, value):
        stat = self.cache.get(name)
        if stat == 0:
            self._update_stat(name, value)
        else:
            self._update_stat(name, stat + value)

    def total(self, name):
        return self.cache.get(name)

    def set(self, name, value):
        self._update_stat(name, value)
