import cProfile
import threading
import traceback

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Stats import Stats
from TorrentSrc.Util.Stats import PyStats


class ThreadManager:

    threads = []

    @staticmethod
    def add_thread(thread):
        ThreadManager.threads.append(thread)

    @staticmethod
    def thread_count():
        return len(ThreadManager.threads)

    @staticmethod
    def remove_thread(thread):
        ThreadManager.threads.remove(thread)


class CustomThread:

    def __init__(self, target, thread_name, args=[]):
        self.target = target
        self.args = args
        self.thread = threading.Thread(target=self.__run)
        self.thread.daemon = True
        self.thread_name = thread_name
        ThreadManager.add_thread(self)
        Stats['threads_started'].add(1)

    def start(self):
        self.thread.start()

    def __run(self):
        try:
            prof = cProfile.Profile()
            prof.enable()
            self.target(*self.args)
            prof.disable()
            PyStats.add_stats(prof)
            ThreadManager.remove_thread(self)
        except Exception:
            excep = str(traceback.format_exc())
            Logger.write(3, "Unhandled exception in thread " + self.thread_name)
            Logger.write(3, excep, 'error')
            EventManager.throw_event(EventType.Error, ["thread_error", "Unknown error in thread " + self.thread_name + ": " + excep])
            ThreadManager.remove_thread(self)

    def join(self):
        self.thread.join()
