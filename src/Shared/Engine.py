from time import sleep

from Shared.Events import EventManager
from Shared.Events import EventType
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread
from Shared.Timing import Timing
from Shared.Util import current_time


class Engine(LogObject):

    def __init__(self, name, tick_time=1000, parent=None):
        super().__init__(parent, "Engine:" + name)

        self.name = name
        self.tick_time = tick_time
        self.last_tick = 0
        self.running = False
        self.thread = None
        self.work_items = []

        self.current_item = None
        self.start_time = 0

        self.timing = dict()
        self.own_time = TimingObject(self.name)

        # Log props
        self.current_item_log = ""

    def runner(self):
        while self.running:
            sleep(0.01)
            if not self.running:
                break

            self.last_tick = current_time()
            self.tick()

    def start(self):
        self.running = True
        self.thread = CustomThread(self.runner, self.name)
        self.thread.start()

    def add_work_item(self, name, interval, work_item, initial_invoke=True):
        self.work_items.append(EngineWorkItem(self, name, interval, work_item, initial_invoke))

    def stop(self):
        self.running = False
        self.thread.join()

    def tick(self):
        tick_time = current_time()
        cur_list = list(self.work_items)
        for i in range(len(cur_list)):
            work_item = cur_list[i]

            if work_item.last_run_time + work_item.interval < tick_time:
                Timing().start_timing("Engine item " + work_item.name)
                self.current_item = work_item
                self.current_item_log = work_item.name
                self.start_time = current_time()
                if not self.running:
                    return

                result = work_item.action()
                self.current_item = None
                self.current_item_log = ""
                test_time = current_time()
                work_item.last_run_time = test_time
                work_item.last_run_duration = test_time - self.start_time

                if work_item.interval == -1:
                    self.work_items.remove(work_item)

                elif not result:
                    self.work_items.remove(work_item)

                if work_item.name not in self.timing:
                    self.timing[work_item.name] = TimingObject(work_item.name)
                self.timing[work_item.name].add_time(current_time() - self.start_time)
                Timing().stop_timing("Engine item " + work_item.name)
                sleep(0)

        self.own_time.add_time(current_time() - tick_time)


class EngineWorkItem(LogObject):

    def __init__(self, parent, name, interval, action, initial_invoke):
        super().__init__(parent, name)

        self.name = name
        self.interval = interval
        self.action = action
        self.last_run_time = 0
        if not initial_invoke:
            self.last_run_time = current_time()
        self.last_run_duration = 0


class TimingObject:

    def __init__(self, name):
        self.name = name
        self.ticks = 0
        self.time = 0

    def add_time(self, time):
        self.ticks += 1
        self.time += time

    def print(self):
        if self.ticks > 1:
            return "Object " + self.name + " averages " + str(self.time/self.ticks) + "ms over " + str(self.ticks) + " ticks"
        return "Object " + self.name + " no stats yet"
