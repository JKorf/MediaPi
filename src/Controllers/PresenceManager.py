import subprocess
import time

import sys

from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread
from Shared.Util import Singleton, current_time


class PresenceManager(metaclass=Singleton):

    def __init__(self):
        self.check_thread = CustomThread(self.check_presence, "Presence checker")
        self.running = False
        self.check_interval = 10
        self.device_gone_interval = 120
        self.on_coming_home = None
        self.on_leaving_home = None
        self.anyone_home = True
        self.pi = sys.platform == "linux" or sys.platform == "linux2"

        self.device_states = [
            DeviceState("Mobiel Jan", "192.168.2.51", self.device_gone_interval),
            DeviceState("Mobiel Melissa", "192.168.2.50", self.device_gone_interval),
        ]

    def start(self):
        self.running = True
        self.check_thread.start()

    def stop(self):
        self.running = False
        self.check_thread.join()

    def check_presence(self):
        if not self.pi:
            return

        while self.running:
            for device in self.device_states:
                result = subprocess.call('sudo arping -q -c1 -W 1 ' + device.ip + ' > /dev/null', shell=True)
                device.set_device_state(result == 0)

            if self.anyone_home and len([x for x in self.device_states if x.home_state]) == 0:
                # left
                if self.on_leaving_home is not None:
                    self.on_leaving_home()
            elif not self.anyone_home and len([x for x in self.device_states if x.home_state]) > 0:
                # returned
                if self.on_coming_home is not None:
                    self.on_coming_home()

            time.sleep(self.check_interval)


class DeviceState:

    def __init__(self, name, ip, gone_interval):
        self.name = name
        self.ip = ip
        self.gone_interval = gone_interval
        self.home_state = True
        self.last_home_state = True
        self.timeout_start_time = 0
        self.last_seen = 0

    def set_device_state(self, home):
        if home:
            self.last_seen = current_time()
            if not self.home_state:
                self.home_state = True
                self.last_home_state = True
                Logger().write(LogVerbosity.Info, "Device " + self.name + " came home")
            return

        if not home and not self.home_state:
            # still not home
            return

        if self.last_home_state:
            # Now not home, last state was home. Start timing
            self.last_home_state = False
            self.timeout_start_time = current_time()
            Logger().write(LogVerbosity.Debug, "Device " + self.name + " not detected, starting leaving timeout")
            return
        else:
            # Now not home, last state was also not home. Check timeout
            if current_time() - self.timeout_start_time > self.gone_interval * 1000:
                self.home_state = False
                Logger().write(LogVerbosity.Info, "Device " + self.name + " left home")

