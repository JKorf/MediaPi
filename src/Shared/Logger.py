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
        self.log_level = 0
        self.log_time = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')

        self.raspberry = sys.platform == "linux" or sys.platform == "linux2"
        self.log_path = Settings.get_string("base_folder") + "/Logs/" + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')

        self.file_size = 0
        self.exception_lock = threading.Lock()
        self.running = False

        self.last_id = 1
        self.last_id_lock = threading.Lock()

        self.log_processor = LogProcessor(self.log_path, 'log_' + self.log_time, True and not self.raspberry)
        self.state_log_processor = LogProcessor(self.log_path, 'state_' + self.log_time, False)

    def start(self, log_level):
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

        print("Log path: " + self.log_path)

        if self.raspberry:
            sys.stdout = StdOutWriter(self.write_print)
            sys.stderr = StdOutWriter(self.write_print)

        self.log_level = log_level

        self.log_processor.start()
        self.state_log_processor.start()

        self.log_processor.enqueue("Time".ljust(14) + " | "
                    + "Thread".ljust(30) + " | "
                    + "File/Line number".ljust(35) + " | "
                    + "Function".ljust(25) + " | "
                    + "Priority".ljust(9) + " | "
                    + "Message\r\n"
                    + "-" * 140 + "\r\n")

    def stop(self):
        self.log_processor.stop()
        self.state_log_processor.stop()

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

            self.log_processor.enqueue(str_info)

    def write_print(self, message):
        self.log_processor.enqueue(message)

    def create_state_object(self, id, name):
        self.state_log_processor.enqueue("{}|{}|{}|{}".format(1, datetime.datetime.utcnow().strftime('%H:%M:%S.%f')[:-3], id, name))

    def update_state(self, id, property, value):
        self.state_log_processor.enqueue("{}|{}|{}|{}|{}".format(2, datetime.datetime.utcnow().strftime('%H:%M:%S.%f')[:-3], id, property, str(value)))

    def finish_state_object(self, id):
        self.state_log_processor.enqueue("{}|{}|{}".format(3, datetime.datetime.utcnow().strftime('%H:%M:%S.%f')[:-3], id))

    def write_error(self, e, additional_info=None):
        with self.exception_lock:
            self.write(LogVerbosity.Important, "Error occurred: " + str(type(e).__name__) + ", more information in the error log")
            with open(self.log_path + '/error_' + type(e).__name__ + '_' + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f')[:-3] + ".txt", 'ab', buffering=0) as file:
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

    @staticmethod
    def format_item(item_time, thread_name, file_name, line, function, priority, message):
        return item_time.strftime('%H:%M:%S.%f')[:-3].ljust(14) + " | " \
            + thread_name.ljust(30) + " | " \
            + (file_name + " #" + str(line)).ljust(35) + " | " \
            + function.ljust(25) + " | " \
            + str(priority)[13:].ljust(9) + " | " \
            + message

    @staticmethod
    def get_log_files():
        list_of_files = glob.glob(Settings.get_string("base_folder") + "/Logs/*/*.txt")
        latest_files = sorted(list_of_files, key=os.path.getctime, reverse=True)
        return [(os.path.basename(x), x, os.path.getsize(x)) for x in latest_files]

    @staticmethod
    def get_log_file(file):
        if not file.endswith(".txt"):
            raise Exception("Not a log file")

        with open(file) as f:
            return "\r\n".join(f.readlines())

    def next_id(self):
        with self.last_id_lock:
            self.last_id += 1
            return self.last_id


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


class LogProcessor:

    def __init__(self, base_path, file_name, print_to_output):
        self.base_path = base_path
        self.base_file_name = file_name
        self.print_to_output = print_to_output
        self.file = None
        self.file_size = 0
        self.file_number = 1
        self.max_log_file_size = Settings.get_int("max_log_file_size")

        self.running = True

        self.process_thread = None
        self.queue = []
        self.queue_event = threading.Event()
        self.queue_lock = threading.Lock()

    def start(self):
        self.create_log_file(self.base_file_name + " #1.txt")
        self.running = True

        self.process_thread = threading.Thread(name="Logger thread", target=self.process, daemon=False)
        self.process_thread.start()

    def create_log_file(self, file_name):
        self.file_size = 0
        self.file = open(self.base_path + '/' + file_name, 'ab', buffering=0)

    def stop(self):
        self.running = False
        self.process_thread.join()
        self.file.close()

    def enqueue(self, item):
        with self.queue_lock:
            self.queue.append(item)
            self.queue_event.set()

    def process(self):
        while True:
            self.queue_event.wait(0.1)
            with self.queue_lock:
                self.queue_event.clear()
                items = list(self.queue)
                item_count = len(items)
                if item_count == 0:
                    continue

                self.queue.clear()

            total = "\r\n".join(items)
            try:
                if self.print_to_output:
                    print(total)

                byte_data = (total + "\r\n").encode('utf8')
                self.file.write(byte_data)
                self.file_size += len(byte_data)
                self.check_file_size()
                time.sleep(0)
            except Exception as e:
                Logger().write_error(e, "Exception during logging")

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
            self.file_number += 1
            file_name = self.base_file_name
            file_name += " #" + str(self.file_number) + ".txt"

            self.create_log_file(file_name)
            self.file.write(b"Continue after max file size was reached\r\n")


class LogItemTracker:

    def __init__(self, parent_id, name):
        self.id = Logger().next_id()
        self.parent_id = parent_id
        self.name = name
        self.id = str(self.parent_id) + ";" + str(self.id)

        Logger().create_state_object(self.id, self.name)

    def update(self, prop, value):
        Logger().update_state(self.id, prop, value)

    def finish(self):
        Logger().finish_state_object(self.id)
