import threading

from Shared.LogObject import LogObject
from Shared.Logger import Logger
from Shared.Util import current_time, Singleton


class ThreadManager(LogObject, metaclass=Singleton):

    def __init__(self):
        super().__init__(None, "Threads")
        self.threads = []
        self.thread_history = dict()
        self.thread_count = 0

    def add_thread(self, thread):
        thread.history_entry = ThreadEntry(thread.thread_name, current_time())
        if thread.thread_name not in self.thread_history:
            self.thread_history[thread.thread_name] = []
        self.thread_history[thread.thread_name].append(thread.history_entry)
        self.threads.append(thread)
        self.thread_count = len(self.threads)

    def remove_thread(self, thread):
        thread.history_entry.end_time = current_time()
        self.threads.remove(thread)
        self.thread_count = len(self.threads)


class ThreadEntry:

    def __init__(self, name, start_time):
        self.thread_name = name
        self.start_time = start_time
        self.end_time = 0


class CustomThread(LogObject):

    @property
    def is_alive(self):
        return self.thread.is_alive

    def __init__(self, target, thread_name, args=[]):
        super().__init__(ThreadManager(), "Thread " + thread_name)

        self.target = target
        self.args = args
        self.thread = threading.Thread(name=thread_name, target=self.__run)
        self.thread.daemon = True
        self.thread_name = thread_name
        self.start_time = 0
        self.history_entry = None

    def start(self):
        self.start_time = current_time()
        ThreadManager().add_thread(self)
        self.thread.start()

    def __run(self):
        try:
            self.target(*self.args)
            ThreadManager().remove_thread(self)
            self.finish()
        except Exception as e:
            Logger().write_error(e, "Exception in thread " + self.thread_name)
            ThreadManager().remove_thread(self)
            self.finish()

    def join(self):
        if threading.current_thread() is not self.thread:
            self.thread.join()
