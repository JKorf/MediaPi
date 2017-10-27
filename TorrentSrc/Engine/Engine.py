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

        self.timing = dict()
        self.timing['ticks'] = 0
        self.timing['engine'] = 0

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

    def stop(self):
        self.running = False
        EventManager.deregister_event(self.event_id)

    def tick(self):
        tick_time = current_time()
        cur_list = list(self.work_items)
        for i in range(len(cur_list)):
            work_item = cur_list[i]

            if work_item.last_run_time + work_item.interval < tick_time:
                start_time = current_time()
                result = work_item.action()
                test_time = current_time()
                work_item.last_run_duration = test_time - start_time
                work_item.last_run_time = test_time
                if self.tick_time > 100:
                    if work_item.name not in self.timing:
                        self.timing[work_item.name] = 0
                    self.timing[work_item.name] += work_item.last_run_duration

                if work_item.interval == -1:
                    self.work_items.remove(work_item)

                elif not result:
                    self.work_items.remove(work_item)

        if self.tick_time > 100:
            if self.timing['ticks'] > 100:
                if self.timing['engine'] / self.timing['ticks'] > self.tick_time:
                    for key, value in self.timing.items():
                        if key == "ticks":
                            continue
                        self.timing[key] = 0
                self.timing['ticks'] = 0
                self.timing['engine'] = 0

            self.timing['ticks'] += 1
            self.timing['engine'] += current_time() - tick_time

    def log(self):
        if self.tick_time > 100 and self.timing['ticks'] > 0:
            Logger.write(2, "Engine " + self.name + " time: " + str(self.timing['engine'] / self.timing['ticks']) + " of " + str(self.tick_time) + ", " + str(self.timing['ticks']) + " ticks")
            for key, value in self.timing.items():
                if key == "ticks":
                    continue

                Logger.write(2, "Sub " + key + ": " + str(value / self.timing['ticks']))
                self.timing[key] = 0

class EngineWorkItem:

    def __init__(self, name, interval, action):
        self.name = name
        self.interval = interval
        self.action = action
        self.last_run_time = 0
        self.last_run_duration = 0

