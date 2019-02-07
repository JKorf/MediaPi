from threading import Lock

from Database.Database import Database
from Shared.Engine import Engine
from Shared.Observable import Observable
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

    lock = Lock()
    cache = StatList()

    def __init__(self):
        self.engine = Engine("Stat saver")
        self.engine.add_work_item("Save stat", 10000, self.save_stats, False)

    def start(self):
        stats = Database().get_stats()
        with Stats.lock:
            for key, value, last_change in stats:
                Stats.cache.update(key, value)

        self.engine.start()

    @staticmethod
    def _update_stat(name, value):
        with Stats.lock:
            Stats.cache.update(name, value)

    @staticmethod
    def save_stats():
        with Stats.lock:
            copy = Stats.cache.statistics.copy()

        for key, val in copy.items():
            Database().update_stat(key, val)
        return True

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
