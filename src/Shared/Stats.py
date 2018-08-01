from Shared.Util import write_size


class MetaStats(type):
    stats = dict()

    def __getitem__(self, item):
        if item not in MetaStats.stats:
            MetaStats.stats[item] = Stat(item)

        return MetaStats.stats[item]


class Stats(object, metaclass=MetaStats):
    pass


class Stat:

    @property
    def average(self):
        if self.counts == 0:
            return 0
        return self.value // self.counts

    @property
    def total(self):
        return self.value

    def __init__(self, name):
        self.name = name
        self.value = 0
        self.counts = 0

    def add(self, val):
        self.value += val
        self.counts += 1

    def set(self, val):
        self.value = val
        self.counts = 1

    def as_size(self):
        return write_size(self.value)
