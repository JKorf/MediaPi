import subprocess

import sys

from Shared.Engine import Engine
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import Singleton


class WiFiController(LogObject, metaclass=Singleton):

    def __init__(self):
        super().__init__(None, "WIFI")

        self.engine = Engine("WiFi processor")
        self.engine.add_work_item("WiFi watcher", 15000, self.watch_wifi, False)
        self.pi = sys.platform == "linux" or sys.platform == "linux2"
        self.quality = 0

    def start(self):
        self.engine.start()

    def watch_wifi(self):
        if self.pi:
            proc = subprocess.Popen(["iwgetid"], stdout=subprocess.PIPE, universal_newlines=True)
            out, err = proc.communicate()
            network_ssid = out.split(":")[1]

            proc = subprocess.Popen(["iwlist", "wlan0", "scan"], stdout=subprocess.PIPE, universal_newlines=True)
            out, err = proc.communicate()
            cells = out.split("Cell ")
            cell_lines = [x for x in cells if network_ssid in x]
            if len(cell_lines) != 0:
                network_lines = cell_lines[0]
                for line in network_lines.split("\n"):
                    if "Quality" in line:
                        fields = line.split("  ")
                        for field in fields:
                            field.replace(" ", "")
                            if len(field) <= 2:
                                continue

                            key_value = field.split("=")
                            if len(key_value) == 1:
                                key_value = field.split(":")

                            if key_value[0] == "Quality":
                                value_max = key_value[1].split("/")
                                new_val = float(value_max[0]) / float(value_max[1]) * 100
                                if self.quality != new_val:
                                    if self.quality == 0:
                                        Logger().write(LogVerbosity.Debug, "Wifi quality: " + str(new_val))
                                    self.quality = new_val

        else:
            proc = subprocess.Popen(["Netsh", "WLAN", "show", "interfaces"], stdout=subprocess.PIPE, universal_newlines=True)
            out, err = proc.communicate()
            lines = out.split("\n")
            for line in lines:
                if "Signal" in line:
                    split = line.split(":")
                    new_val = float(split[1].replace("%", ""))
                    if self.quality != new_val:
                        if self.quality == 0:
                            Logger().write(LogVerbosity.Debug, "Wifi quality: " + str(new_val))

                        self.quality = new_val

        return True
