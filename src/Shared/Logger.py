import datetime
import glob
import inspect
import ntpath
import os
import threading
import traceback
from enum import Enum
import time

import sys

from Shared.Settings import Settings
from Shared.Util import Singleton


class Logger(metaclass=Singleton):

    def __init__(self):
        self.file = None
        self.log_level = 0
        self.log_thread = None

        self.queue = []
        self.queue_event = threading.Event()
        self.queue_lock = threading.Lock()

        self.raspberry = sys.platform == "linux" or sys.platform == "linux2"
        self.log_path = Settings.get_string("base_folder") + "/Logs/" + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        self.max_log_file_size = Settings.get_int("max_log_file_size")

        self.file_size = 0
        self.exception_lock = threading.Lock()
        self.running = False

    def start(self, log_level):
        self.log_level = log_level
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

        if self.raspberry:
            sys.stdout = StdOutWriter(self.write_print)
            sys.stderr = StdOutWriter(self.write_print)

        self.create_log_file()
        self.running = True

        self.log_thread = threading.Thread(name="Logger thread", target=self.process_queue, daemon=False)
        self.log_thread.start()

        print("Log location: " + self.log_path)

    def stop(self):
        self.running = False
        self.queue_event.set()
        self.log_thread.join()

    def create_log_file(self):
        self.file_size = 0
        self.file = open(self.log_path + '/log_' + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + ".txt", 'ab', buffering=0)
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
            self.queue_event.wait(0.1)
            with self.queue_lock:
                self.queue_event.clear()
                items = list(self.queue)
                item_count = len(items)
                if item_count == 0:
                    continue

                if item_count > 50:
                    items.append(self.format_item(datetime.datetime.utcnow(), "-", "-", 0, "-", LogVerbosity.Debug, "Processed " + str(item_count) + " log items this round"))

                self.queue.clear()

            total = "\r\n".join(items)
            try:
                if not self.raspberry:
                    print(total)

                byte_data = (total + "\r\n").encode('utf8')
                self.file.write(byte_data)
                self.file_size += len(byte_data)
                self.check_file_size()
            except Exception as e:
                self.write_error(e, "Exception during logging")

            if not self.running:
                # If stopped, wait for 100 ms and if nothing gets added stop
                time.sleep(0.1)
                with self.queue_lock:
                    if len(self.queue) == 0:
                        break

    def check_file_size(self):
        if self.file_size > self.max_log_file_size:
            self.file.write(b"Max file size reached, continue in new file")
            self.file.close()
            self.create_log_file()
            self.file.write(b"Continue after max file size was reached\r\n")

    def write_print(self, message):
        with self.queue_lock:
            self.queue.append(message)
            self.queue_event.set()

    def write(self, log_priority, message):
        if self.log_level <= log_priority.value:
            info = inspect.getframeinfo(sys._getframe().f_back)
            str_info = self.format_item(
                datetime.datetime.utcnow(),
                threading.currentThread().getName(),
                path_leaf(info.filename),
                info.lineno,
                info.function,
                log_priority,
                message)

            with self.queue_lock:
                self.queue.append(str_info)
                self.queue_event.set()

    def write_error(self, e, additional_info=None):
        with self.exception_lock:
            self.write(LogVerbosity.Important, "Error ocured: " + str(type(e).__name__)+ ", more information in the error log")
            with open(self.log_path + '/error_'+ type(e).__name__ + '_' + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + ".txt", 'ab',
                             buffering=0) as file:
                file.write(b'Time:'.ljust(20) + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S').encode('utf-8') + b'\r\n')
                file.write(b'Error:'.ljust(20) + type(e).__name__.encode('utf-8') + b'\r\n')
                if additional_info is not None:
                    file.write(b'Info:'.ljust(20) + additional_info.encode('utf-8') + b'\r\n')
                file.write(b'Call stack:'.ljust(20) + b'\r\n')
                e_traceback = traceback.format_exception(e.__class__, e, e.__traceback__)
                for line in e_traceback:
                    file.write(line.encode('utf-8') + b'\r\n')
                    if not self.raspberry:
                        print(e_traceback)

    def format_item(self, time, thread_name, file_name, line, function, priority, message):
        return time.strftime('%H:%M:%S.%f')[:-3].ljust(14) + " | " \
            + thread_name.ljust(30) + " | " \
            + (file_name + " #" + str(line)).ljust(35) + " | " \
            + function.ljust(25) + " | " \
            + str(priority)[13:].ljust(9) + " | " \
            + message

    def get_log_files(self):
        list_of_files = glob.glob(Settings.get_string("base_folder") + "/Logs/*/*.txt")
        latest_files = sorted(list_of_files, key=os.path.getctime, reverse=True)
        return [(os.path.basename(x), x, os.path.getsize(x)) for x in latest_files]

    def get_log_file(self, file):
        if not file.endswith(".txt"):
            raise Exception("Not a log file")

        with open(file) as f:
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


class StdOutWriter:

    def __init__(self, write_function):
        self.write_function = write_function
        self.closed = False

    def write(self, data):
        try:
            data = data.decode()
        except AttributeError:
            pass

        if data == '\n':
            return

        self.write_function(data.rstrip())

    def flush(self):
        pass