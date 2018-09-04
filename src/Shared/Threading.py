import threading
import traceback

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Stats import Stats
from Shared.Util import current_time


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
        self.thread = threading.Thread(name=thread_name, target=self.__run)
        self.thread.daemon = True
        self.thread_name = thread_name
        self.start_time = 0
        ThreadManager.add_thread(self)
        Stats.add('threads_started', 1)

    def start(self):
        self.start_time = current_time()
        self.thread.start()

    def __run(self):
        try:
            self.target(*self.args)
            ThreadManager.remove_thread(self)
        except Exception:
            excep = str(traceback.format_exc())
            Logger.write(3, "Unhandled exception in thread " + self.thread_name)
            Logger.write(3, excep, 'error')
            EventManager.throw_event(EventType.Error, ["thread_error", "Unknown error in thread " + self.thread_name + ": " + excep])
            ThreadManager.remove_thread(self)

    def join(self):
        self.thread.join()
