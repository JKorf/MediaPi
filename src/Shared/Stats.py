from threading import Lock

from Database.Database import Database
from Shared.Engine import Engine
from Shared.Util import Singleton


class Stats(metaclass=Singleton):

    lock = Lock()
    cache = dict()

    def __init__(self):
        self.engine = Engine("Stat saver")
        self.engine.add_work_item("Save stat", 10000, self.save_stats, False)

    def start(self):
        self.engine.start()

    @staticmethod
    def _get_stat(name):
        if name not in Stats.cache:
            if Database() is not None:
                stat = Database().get_stat(name)
            else:
                stat = 0
            Stats.cache[name] = stat
        else:
            return Stats.cache[name]
        return stat

    @staticmethod
    def _update_stat(name, value):
        with Stats.lock:
            Stats.cache[name] = value

    @staticmethod
    def save_stats():
        with Stats.lock:
            copy = Stats.cache.copy()

        for key, val in copy.items():
            Database().update_stat(key, val)

    @staticmethod
    def add(name, value):
        stat = Stats._get_stat(name)
        if stat == 0:
            Stats._update_stat(name, value)
        else:
            Stats._update_stat(name, stat + value)

    @staticmethod
    def total(name):
        return Stats._get_stat(name)

    @staticmethod
    def set(name, value):
        Stats._update_stat(name, value)
