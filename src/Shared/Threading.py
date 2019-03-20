import threading

from Shared.Logger import Logger
from Shared.Util import current_time


class ThreadManager:

    threads = []
    thread_history = dict()

    @staticmethod
    def add_thread(thread):
        thread.history_entry = ThreadEntry(thread.thread_name, current_time())
        if thread.thread_name not in ThreadManager.thread_history:
            ThreadManager.thread_history[thread.thread_name] = []
        ThreadManager.thread_history[thread.thread_name].append(thread.history_entry)
        ThreadManager.threads.append(thread)

    @staticmethod
    def thread_count():
        return len(ThreadManager.threads)

    @staticmethod
    def remove_thread(thread):
        thread.history_entry.end_time = current_time()
        ThreadManager.threads.remove(thread)


class ThreadEntry:

    def __init__(self, name, start_time):
        self.thread_name = name
        self.start_time = start_time
        self.end_time = 0


class CustomThread:

    @property
    def is_alive(self):
        return self.thread.is_alive

    def __init__(self, target, thread_name, args=[]):
        self.target = target
        self.args = args
        self.thread = threading.Thread(name=thread_name, target=self.__run)
        self.thread.daemon = True
        self.thread_name = thread_name
        self.start_time = 0
        self.history_entry = None
        ThreadManager.add_thread(self)

    def start(self):
        self.start_time = current_time()
        self.thread.start()

    def __run(self):
        try:
            self.target(*self.args)
            ThreadManager.remove_thread(self)
        except Exception as e:
            Logger().write_error(e, "Exception in thread " + self.thread_name)
            ThreadManager.remove_thread(self)

    def join(self):
        if threading.current_thread() is not self.thread:
            self.thread.join()
