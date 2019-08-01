import os
from subprocess import PIPE

import psutil
import time

import sys

from eventlet import greenio
from eventlet.green import subprocess

from MediaPlayer.MediaManager import MediaManager
from Shared.Events import EventManager, EventType
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import Singleton


class StateManager(metaclass=Singleton):

    def __init__(self):
        self.state_data = StateData()
        self.monitoring = sys.platform == "linux" or sys.platform == "linux2"
        self.state_data.name = Settings.get_string("name")
        self.watch_thread = CustomThread(self.update_state, "State observer")
        self.watch_thread.start()
        self.memory_thread = CustomThread(self.check_memory, "Memory observer")
        self.memory_thread.start()

    def update_state(self):
        boot_time = psutil.boot_time()

        while True:
            self.state_data.start_update()
            self.state_data.memory = psutil.virtual_memory().percent
            self.state_data.cpu = psutil.cpu_percent()
            self.state_data.threads = ThreadManager().thread_count
            self.state_data.temperature = self.get_temperature()
            disk_info = psutil.disk_usage("/" if self.monitoring else "C:/")
            self.state_data.disk_total = disk_info.total
            self.state_data.disk_used = disk_info.used
            self.state_data.disk_free = disk_info.free
            self.state_data.disk_percentage = disk_info.percent
            self.state_data.boot_time = boot_time
            self.state_data.stop_update()
            time.sleep(1)

    def check_memory(self):
        if not self.monitoring:
            return

        while True:
            if self.state_data.memory > 90:
                Logger().write(LogVerbosity.Info, "Memory high ( " + str(self.state_data.memory) + "% )")

            time.sleep(10)

    def get_temperature(self):
        if not self.monitoring:
            return "-"
        proc = subprocess.Popen(["vcgencmd", "measure_temp"], stdout=PIPE, universal_newlines=True)
        out, err = proc.communicate()
        return out.replace("temp=", "")


class StateData(Observable):

    def __init__(self):
        super().__init__("StateData", 1)
        self.name = None
        self.memory = 0
        self.temperature = 0
        self.cpu = 0
        self.threads = 0
        self.disk_used = 0
        self.disk_total = 0
        self.disk_percentage = 0
        self.disk_free = 0
        self.boot_time = 0
