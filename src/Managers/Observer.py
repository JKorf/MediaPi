import subprocess
import time
import urllib.parse

from Shared.Events import EventType, EventManager
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Threading import CustomThread
from Shared.Util import current_time


class Observer:
    @property
    def torrent(self):
        return self.start.torrent_manager.torrent

    @property
    def player(self):
        return self.start.gui_manager.player

    def __init__(self, start):
        self.start = start
        self.added_unfinished = False
        self.removed_unfinished = False
        self.last_play_update_time = 0

        self.is_slave = Settings.get_bool("slave")
        self.master_path = Settings.get_string("master_ip") + ":50010/file/"

        EventManager.register_event(EventType.StartPlayer, self.start_player)
        EventManager.register_event(EventType.PreparePlayer, self.start_player)

        thread = CustomThread(self.watch_download_speed, "Watch download speed")
        thread.start()
        thread = CustomThread(self.update_unfinished, "Watch unfinished")
        thread.start()

        if Settings.get_bool("show_gui"):
            thread = CustomThread(self.watch_wifi, "Watch wifi")
            thread.start()

    def start_player(self, type=None, title=None, url=None, img=None, position=0, media_file=None):
        self.added_unfinished = False
        self.removed_unfinished = False

    def watch_download_speed(self):
        while True:
            if self.torrent is not None:
                # Check max download speed
                current = Stats['max_download_speed'].total
                if self.torrent.download_counter.max > current:
                    Stats['max_download_speed'].set(self.torrent.download_counter.max)

            time.sleep(5)

    def update_unfinished(self):
        while True:
            if not self.player.path:
                time.sleep(5)
                continue

            watching_type = "torrent"
            if self.player.type == "File":
                watching_type = "file"

            media_file = None
            if self.torrent is not None:
                if self.torrent.media_file is not None:
                    media_file = self.torrent.media_file.name
                path = self.torrent.uri
            else:
                path = self.player.path

            if path.startswith(self.master_path):
                path = path[len(self.master_path):]

            img = self.player.img
            if not img:
                img = ""

            # Update time for resuming
            if self.player.get_position() > 0 and self.player.get_length() - self.player.get_position() < 30:
                # Remove unfinished, we're < 30 secs from end
                if not self.removed_unfinished:
                    self.removed_unfinished = True
                    if self.is_slave:
                        self.start.webserver_manager.server.notify_master("/database/remove_unfinished?url=" + urllib.parse.quote(path))
                    else:
                        self.start.database.remove_watching_item(path)

            elif self.player.get_position() > 10 and not self.added_unfinished and not self.removed_unfinished:
                # Add unfinished
                self.added_unfinished = True
                if self.is_slave:
                    notify_url = "/database/add_unfinished?url=" + urllib.parse.quote(path) + "&name=" + urllib.parse.quote(self.player.title) + "&length=" + str(self.player.get_length()) \
                                                                + "&time=" + str(current_time()) + "&image=" + urllib.parse.quote(img) + "&type=" + watching_type
                    if media_file is not None:
                        notify_url += "&mediaFile=" + urllib.parse.quote(media_file)
                    self.start.webserver_manager.server.notify_master(notify_url)
                else:
                    self.start.database.add_watching_item(watching_type, self.player.title, path, self.player.img, self.player.get_length(), current_time(), media_file)

            if not self.removed_unfinished and self.player.get_position() > 10:
                # Update unfinished
                pos = self.player.get_position()
                if self.last_play_update_time != pos:
                    self.last_play_update_time = pos
                    if self.is_slave:
                        notify_url = "/database/update_unfinished?url=" + urllib.parse.quote(path) + "&position=" + str(pos) + "&watchedAt=" + str(current_time())
                        if media_file is not None:
                            notify_url += "&mediaFile=" + urllib.parse.quote(media_file)
                        self.start.webserver_manager.server.notify_master(notify_url)
                    else:
                        self.start.database.update_watching_item(path, pos, current_time(), media_file)

            time.sleep(5)

    def watch_wifi(self):
        rasp = Settings.get_bool("raspberry")
        if rasp:
            proc = subprocess.Popen(["iwgetid"], stdout=subprocess.PIPE, universal_newlines=True)
            out, err = proc.communicate()
            network_ssid = out.split(":")[1]

        while True:
            if not self.start.gui_manager.gui:
                time.sleep(5)
                continue

            if rasp:
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
                                    self.start.gui_manager.gui.set_wifi_quality(float(value_max[0]) / float(value_max[1]) * 100)
            else:
                proc = subprocess.Popen(["Netsh", "WLAN", "show", "interfaces"], stdout=subprocess.PIPE, universal_newlines=True)
                out, err = proc.communicate()
                lines = out.split("\n")
                for line in lines:
                    if "Signal" in line:
                        split = line.split(":")
                        self.start.gui_manager.gui.set_wifi_quality(float(split[1].replace("%", "")))

            time.sleep(15)
