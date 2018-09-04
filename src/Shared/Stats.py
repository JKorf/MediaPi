
class Stats:

    database = None

    @staticmethod
    def add(name, value):
        stat = Stats.database.get_stat(name)
        if stat == 0:
            Stats.database.update_stat(name, value)
        else:
            Stats.database.update_stat(name, stat + value)

    @staticmethod
    def total(name):
        return Stats.database.get_stat(name)

    @staticmethod
    def set(name, value):
        Stats.database.update_stat(name, value)
