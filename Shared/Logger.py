import datetime
import inspect
import ntpath
import os
from threading import RLock

from Shared.Settings import Settings


class Logger:

    log_level = 1
    file = None
    lock = RLock()

    @staticmethod
    def set_log_level(level):
        Logger.log_level = level

    @staticmethod
    def write(log_priority, message, type='info'):
        if Logger.file is None:
            log_path = Settings.get_string("log_folder")
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            Logger.file = open(log_path + '/log_'+datetime.date.today().strftime('%d-%m-%Y') + ".txt", 'ab', buffering=0)
            Logger.file.write("\r\n".encode('ascii'))
            Logger.file.write("--------------------------------------- Start up ----------------------------------------\r\n".encode('ascii'))
            Logger.file.write("\r\n".encode('ascii'))
            print("Log location: " + log_path)

        if Logger.log_level <= log_priority:
            info = get_info()
            strInfo = datetime.datetime.utcnow().strftime('%H:%M:%S.%f')[:-3].ljust(14) + " | "\
                      + path_leaf(info.filename).ljust(25) + " | "\
                      + info.function.ljust(20) + " | #"\
                      + str(info.lineno).ljust(5) + " | "\
                      + str(type).ljust(7) + " | "\
                      + message
            file_log = strInfo
            if type == 'error':
                strInfo = "\033[91m" + strInfo + "\033[0m"

            if log_priority == 3:
                strInfo = '\033[1m' + strInfo + '\033[0m'
            Logger.lock.acquire()
            if not Settings.get_bool("raspberry"):
                print(strInfo)

            Logger.file.write((file_log + "\r\n").encode('ascii'))
            Logger.lock.release()


def get_info():
    caller_frame_record = inspect.stack()[2]
    frame = caller_frame_record[0]
    info = inspect.getframeinfo(frame)
    return info


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)
