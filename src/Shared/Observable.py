from threading import Event

from Shared.Threading import CustomThread
from Shared.Util import current_time


class Observable:

    def __init__(self, name, update_interval):
        self.__name = name
        self.__update_interval = update_interval
        self.__callbacks = []
        self.__changed = True
        self.__last_update = 0
        self.__wait_event = Event()

        self.__update_thread = CustomThread(self.__check_update, name + " update")
        self.__update_thread.start()

    def register_callback(self, cb):
        self.__callbacks.append(cb)

    def updated(self):
        self.__changed = True

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
