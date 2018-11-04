from Shared.Logger import Logger
from Shared.Util import current_time


class Timer:

    def __init__(self, name):
        self.name = name
        self.start_time = current_time()

    def log(self, name=None):
        if not name:
            Logger.write(2, self.name + " timing: " + str(current_time() - self.start_time))
        else:
            Logger.write(2, self.name + " timing at " + name + ": " + str(current_time() - self.start_time))
