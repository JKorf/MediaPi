from Shared.LogObject import LogObject
from Shared.Settings import Settings
from Shared.Util import Singleton, current_time


class Timing(LogObject, metaclass=Singleton):

    def __init__(self):
        super().__init__(None, "Timings")
        self.timings = dict()

    def start_timing(self, name):
        if not Settings.get_bool("state_logging"):
            return

        if name not in self.timings:
            self.timings[name] = TimingData(name)
        self.timings[name].start()

    def stop_timing(self, name):
        if not Settings.get_bool("state_logging"):
            return

        self.timings[name].stop()

    def remove(self, name):
        if not Settings.get_bool("state_logging"):
            return

        self.timings[name].remove()
        del self.timings[name]


class TimingData(LogObject):

    def __init__(self, name):
        super().__init__(Timing(), name)

        self.current_start = 0
        self.name = name

        self.high = 0
        self.low = 0
        self.average = 0
        self.total_items = 0
        self.total_time = 0

    def start(self):
        self.current_start = current_time()

    def stop(self):
        run_time = current_time() - self.current_start
        self.high = max(run_time, self.high)
        self.low = min(run_time, self.low)
        self.total_items += 1
        self.total_time += run_time
        self.average = self.total_time / self.total_items

    def remove(self):
        self.finish()
