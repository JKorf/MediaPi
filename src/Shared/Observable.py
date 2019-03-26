from threading import Event
from collections import namedtuple

from Shared.LogObject import LogObject
from Shared.Logger import Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time


class Observable(LogObject):

    def __init__(self, name, update_interval):
        super().__init__(None, name)

        self.__name = name
        self.__update_interval = update_interval
        self.__callbacks = []
        self.__changed = True
        self.__last_update = 0

        self.__start_state = None
        self.__last_update_state = None

        self.__wait_event = Event()

        self.__update_thread = CustomThread(self.__check_update, name + " update")
        self.__update_thread.start()

    def register_callback(self, cb):
        self.__callbacks.append(cb)
        cb(self, self)

    def start_update(self):
        self.__start_state = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def stop_update(self):
        for k, v in self.__start_state.items():
            if self.__dict__[k] != v:
                self.__changed = True
                self.__wait_event.set()
                break

    def changed(self):
        self.__changed = True
        self.__wait_event.set()

    def reset(self):
        self.start_update()
        for k, v in self.__start_state.items():
            if isinstance(v, int) or isinstance(v, float):
                self.__dict__[k] = 0
            else:
                self.__dict__[k] = None
        self.stop_update()

    def __check_update(self):
        while True:
            self.__wait_event.wait(self.__update_interval)
            self.__wait_event.clear()
            if current_time() - self.__last_update < (self.__update_interval * 1000):
                continue

            if self.__changed:
                self.__changed = False
                self.__last_update = current_time()
                dic = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
                last_update = namedtuple("Observable", dic.keys())(*dic.values())
                for cb in self.__callbacks:
                    try:
                        cb(self.__last_update_state or self, self)
                    except Exception as e:
                        Logger().write_error(e, "Exception in observer callback")
                self.__last_update_state = last_update
