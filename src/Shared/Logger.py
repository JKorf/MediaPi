import datetime
import glob
import inspect
import ntpath
import os
import threading
from enum import Enum
from queue import Queue

import sys

from Shared.Settings import Settings
from Shared.Util import Singleton


class Logger(metaclass=Singleton):

    def __init__(self):
        self.file = None
        self.log_level = 0
        self.log_thread = None
        self.queue = Queue()
        self.raspberry = Settings.get_bool("raspberry")
        self.log_path = Settings.get_string("base_folder") + "/Logs"
        self.max_log_file_size = Settings.get_int("max_log_file_size")

        self.file_size = 0

    def start(self, log_level):
        self.log_level = log_level
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

        self.create_log_file()
        self.log_thread = threading.Thread(name="Logger() thread", target=self.process_queue)
        self.log_thread.start()

        print("Log location: " + self.log_path)

    def create_log_file(self):
        self.file_size = 0
        self.file = open(self.log_path + '/log_' + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".txt", 'ab',
                         buffering=0)
        self.file.write("\r\n".encode('utf8'))
        self.file.write(("Time".ljust(14) + " | "
                         + "Thread".ljust(30) + " | "
                         + "File".ljust(25) + " | "
                         + "Function".ljust(30) + " | #"
                         + "Line".ljust(5) + " | "
                         + "Type".ljust(7) + " | "
                         + "Message\r\n").encode("utf8"))
        self.file.write(("-" * 140 + "\r\n").encode("utf8"))

    def process_queue(self):
        while True:
            item = self.queue.get()
            if not self.raspberry:
                print(item)

            byte_data = (item + "\r\n").encode('utf8')
            self.file.write(byte_data)
            self.file_size += len(byte_data)
            self.check_file_size()

    def check_file_size(self):
        if self.file_size > self.max_log_file_size:
            self.file.write(b"Max file size reached, continue in new file")
            self.file.close()
            self.create_log_file()
            self.file.write(b"Continue after max file size was reached\r\n")

    def write(self, log_priority, message):
        if self.log_level <= log_priority.value:
            info = inspect.getframeinfo(sys._getframe().f_back)
            str_info = datetime.datetime.utcnow().strftime('%H:%M:%S.%f')[:-3].ljust(14) + " | " \
                       + threading.currentThread().getName().ljust(30) + " | " \
                       + (path_leaf(info.filename)+ " #" + str(info.lineno)).ljust(35) + " | " \
                       + info.function.ljust(25) + " | " \
                       + str(log_priority)[13:].ljust(9) + " | " \
                       + message

            self.queue.put(str_info)

    @staticmethod
    def get_log_files():
        list_of_files = glob.glob(Settings.get_string("base_folder") + "/Logs/*.txt")
        latest_files = sorted(list_of_files, key=os.path.getctime, reverse=True)
        return [(os.path.basename(x), os.path.getsize(x)) for x in latest_files]

    @staticmethod
    def get_log_file(file):
        if not file.endswith(".txt"):
            raise Exception("Not a log file")

        with open(Settings.get_string("base_folder") + "/Logs/" + file) as f:
            return "\r\n".join(f.readlines())

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class LogVerbosity(Enum):
    All = 0
    Debug = 1
    Info = 2
    Important = 3
    Nothing = 4
