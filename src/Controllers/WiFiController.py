import subprocess

from Shared.Engine import Engine
from Shared.Events import EventManager, EventType
from Shared.Settings import Settings
from Shared.Util import Singleton


class WiFiController(metaclass=Singleton):

    def __init__(self):
        self.engine = Engine("WiFi Manager")
        self.engine.add_work_item("WiFi watcher", 5000, self.watch_wifi, False)
        self.pi = Settings.get_bool("raspberry")

        self.connected = False

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
                                EventManager.throw_event(EventType.WiFiQualityUpdate, [float(value_max[0]) / float(value_max[1]) * 100])

                                if not self.connected:
                                    self.connected = self.get_actual_address()

        else:
            proc = subprocess.Popen(["Netsh", "WLAN", "show", "interfaces"], stdout=subprocess.PIPE, universal_newlines=True)
            out, err = proc.communicate()
            lines = out.split("\n")
            for line in lines:
                if "Signal" in line:
                    split = line.split(":")
                    EventManager.throw_event(EventType.WiFiQualityUpdate, [float(split[1].replace("%", ""))])
        return True
