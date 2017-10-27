import pstats


class PyStats:

    stats = None

    @classmethod
    def add_stats(cls, profile):
        if PyStats.stats is None:
            PyStats.stats = pstats.Stats(profile)
        else:
            PyStats.stats.add(profile)