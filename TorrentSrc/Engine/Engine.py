from Shared.Util import current_time

from time import sleep

from TorrentSrc.Util.Threading import CustomThread

from Shared.Logger import Logger

from Shared.Events import EventManager

from Shared.Events import EventType


class Engine:

    def __init__(self, name, tick_time):
        self.name = name
        self.tick_time = tick_time
        self.last_tick = 0
        self.running = False
        self.thread = None
        self.work_items = []
        self.overtime = 0

        self.current_item = None
        self.start_time = 0

        self.timing = dict()
        self.own_time = TimingObject(self.name)

        self.event_id = EventManager.register_event(EventType.Log, self.log)

    def runner(self):
        while self.running:
            test_time = current_time()
            remaining_time = self.tick_time - (test_time - self.last_tick)

            if remaining_time < 0:
                remaining_time = 0
            sleep(remaining_time / 1000)
            self.last_tick = current_time()
            if not self.running:
                break

            self.tick()

    def start(self):
        self.running = True
        self.thread = CustomThread(self.runner, self.name)
        self.thread.start()

    def queue_repeating_work_item(self, name, interval, work_item):
        self.work_items.append(EngineWorkItem(name, interval, work_item))

    def queue_single_work_item(self, name, work_item):
        self.work_items.append(EngineWorkItem(name, -1, work_item))

    def invoke_work_item(self, name):
        [x for x in self.work_items if x.name is name][0].last_run_time = 0

    def stop(self):
        self.running = False
        EventManager.deregister_event(self.event_id)

    def tick(self):
        tick_time = current_time()
        cur_list = list(self.work_items)
        for i in range(len(cur_list)):
            work_item = cur_list[i]

            if work_item.last_run_time + work_item.interval < tick_time:
                self.current_item = work_item
                self.start_time = current_time()
                result = work_item.action()
                self.current_item = None
                test_time = current_time()
                work_item.last_run_time = test_time

                if work_item.interval == -1:
                    self.work_items.remove(work_item)

                elif not result:
                    self.work_items.remove(work_item)

                if work_item.name not in self.timing:
                    self.timing[work_item.name] = TimingObject(work_item.name)
                self.timing[work_item.name].add_time(current_time() - self.start_time)

        self.own_time.add_time(current_time() - tick_time)

    def log(self):
        if self.own_time.ticks > 1:
            Logger.lock.acquire()
            log_str = "-- Engine "+self.own_time.print()
            if self.current_item:
                log_str += ", CT: " + str(current_time() - self.start_time) + " @ " + str(self.current_item.name)
            log_str += " --"
            Logger.write(3, log_str)
            for key, value in self.timing.items():
                Logger.write(3, "     " + value.print())
            Logger.lock.release()


class EngineWorkItem:

    def __init__(self, name, interval, action):
        self.name = name
        self.interval = interval
        self.action = action
        self.last_run_time = 0
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
