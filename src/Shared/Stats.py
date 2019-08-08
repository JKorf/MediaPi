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
        self.work_thread = CustomThread(self.save_stats, "Stat saver", [])

    def start(self):
        stats = Database().get_stats()
        for key, value, last_change in stats:
            Stats.cache.update(key, value)

        self.work_thread.start()

    @staticmethod
    def _update_stat(name, value):
        Stats.cache.update(name, value)

    @staticmethod
    def save_stats():
        while True:
            copy = Stats.cache.statistics.copy()
            Logger().write(LogVerbosity.Debug, "Saving stats")
            for key, val in copy.items():
                Database().update_stat(key, val)

            time.sleep(15)

    @staticmethod
    def add(name, value):
        stat = Stats.cache.get(name)
        if stat == 0:
            Stats._update_stat(name, value)
        else:
            Stats._update_stat(name, stat + value)

    @staticmethod
    def total(name):
        return Stats.cache.get(name)

    @staticmethod
    def set(name, value):
        Stats._update_stat(name, value)
