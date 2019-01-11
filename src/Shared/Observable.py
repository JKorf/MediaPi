from threading import Event

from Shared.Logger import Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time


class Observable:

    def __init__(self, name, update_interval):
        self.__name = name
        self.__update_interval = update_interval
        self.__callbacks = []
        self.__changed = True
        self.__last_update = 0
        self.__start_state = None
        self.__wait_event = Event()

        self.__update_thread = CustomThread(self.__check_update, name + " update")
        self.__update_thread.start()

    def register_callback(self, cb):
        self.__callbacks.append(cb)

    def start_update(self):
        self.__start_state = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def stop_update(self):
        for k, v in self.__start_state.items():
            if self.__dict__[k] != v:
                self.__changed = True
                self.__wait_event.set()
                break

    def __check_update(self):
        while True:
            self.__wait_event.wait(self.__update_interval)
            self.__wait_event.clear()
            if current_time() - self.__last_update < (self.__update_interval * 1000):
                continue

            if self.__changed:
                self.__changed = False
                self.__last_update = current_time()
                for cb in self.__callbacks:
                    cb(self)
