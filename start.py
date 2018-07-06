#!/usr/bin/env python3
import json
import os
import subprocess
import urllib.parse

os.chdir(os.path.dirname(__file__))

from Database.Database import Database
from TorrentSrc.Torrent.Torrent import Torrent
from TorrentSrc.Streaming.StreamListener import StreamListener

from DHT.DHTEngine import DHTEngine

from Shared.Util import current_time
from Shared.Events import EventManager, EventType
from Shared.Stats import Stats
from Shared.Logger import Logger
from Shared.Settings import Settings

from TorrentSrc.Util.Threading import CustomThread

from Web.Server.TornadoServer import TornadoServer
from Web.Server.Subtitles.SubtitleProvider import SubtitleProvider
from Web.Server.Controllers.UtilController import UtilController

import sys
import time
import traceback
from subprocess import call

from InterfaceSrc.GUI import GUI
from InterfaceSrc.VLCPlayer import VLCPlayer
from InterfaceSrc.VLCPlayer import PlayerState


class StartUp:

    stats = None

    def __init__(self):
        Logger.set_log_level(Settings.get_int("log_level"))
        Logger.write(2, "Starting")
        sys.excepthook = self.handle_exception

        Stats['start_time'].add(current_time())
        self.gui = None
        self.app = None
        self.player = None
        self.server = None
        self.torrent = None
        self.running = True
        self.youtube_end_counter = 0
        self.is_slave = Settings.get_bool("slave")
        self.master_ip = Settings.get_string("master_ip")

        self.added_unfinished = False
        self.removed_unfinished = False

        if Settings.get_bool("show_gui"):
            self.start_gui()

        if not self.is_slave:
            self.database = Database()
            self.database.init_database()
            self.file_listener = StreamListener("MasterFileServer", 50010)
            self.file_listener.start_listening()

        self.dht_enabled = Settings.get_bool("dht")
        if self.dht_enabled:
            self.dht = DHTEngine()
            self.dht.start()
            EventManager.register_event(EventType.RequestDHTPeers, self.request_dht_peers)

        self.start_webserver()
        self.init_player()
        self.start_stat_observer()
        self.init_sound()
        self.subtitle_provider = SubtitleProvider(self)
        self.init_folders()
        self.last_play_update_time = 0

        version = json.loads(UtilController.version())
        Logger.write(3, "MediaPlayer version " + version['version_number'] + " (" + version['build_date'] + ")")
        Logger.write(3, "Slave: " + str(self.is_slave))
        if self.is_slave:
            Logger.write(3, "Master ip: " + str(Settings.get_string("master_ip")))
        Logger.write(3, "Pi: " + str(Settings.get_bool("raspberry")))

        Logger.write(2, "Started")
        if self.gui is not None:
            self.gui.showFullScreen()
            sys.exit(self.app.exec_())
        else:
            while self.running:
                time.sleep(10)

    def start_webserver(self):
        self.server = TornadoServer(self)
        self.server.start()
        actual_address = self.server.get_actual_address()
        Logger.write(3, "Webserver running on " + actual_address)

        if self.gui is not None:
            self.gui.set_address(actual_address)

    def init_player(self):
        self.player = VLCPlayer()
        self.hook_events()

    def init_sound(self):
        if sys.platform == "linux" or sys.platform == "linux2":
            Logger.write(2, "Settings sound to 100%")
            call(["amixer", "sset", "PCM,0", "100%"])

    def start_gui(self):
        self.app, self.gui = GUI.new_gui(self)

    def start_stat_observer(self):
        thread = CustomThread(self.watch_stats, "Watch playing")
        thread.start()
        thread = CustomThread(self.update_unfinished, "Watch unfinished")
        thread.start()
        thread = CustomThread(self.watch_wifi, "Watch wifi")
        thread.start()

    def watch_stats(self):
        while self.running:
            if self.torrent is not None:
                # Check max download speed
                current = Stats['max_download_speed'].total
                if self.torrent.download_counter.max > current:
                    Stats['max_download_speed'].set(self.torrent.download_counter.max)

            time.sleep(5)

    def update_unfinished(self):
        while self.running:
            if not self.player.path:
                time.sleep(5)
                continue

            watching_type = "torrent"
            if self.player.type == "File":
                watching_type = "file"

            if self.torrent is not None:
                path = self.torrent.uri
            else:
                path = self.player.path

            master_path = self.master_ip + ":50010/file/"
            if path.startswith(master_path):
                path = path[len(master_path):]

            img = self.player.img
            if not img:
                img = ""

            # Update time for resuming
            if self.player.get_position() > 0 and self.player.get_length() - self.player.get_position() < 30:
                # Remove unfinished, we're < 30 secs from end
                if not self.removed_unfinished:
                    self.removed_unfinished = True
                    if self.is_slave:
                        self.server.notify_master("/database/remove_unfinished?url=" + urllib.parse.quote(path))
                    else:
                        self.database.remove_watching_item(path)

            elif self.player.get_position() > 10 and not self.added_unfinished and not self.removed_unfinished:
                # Add unfinished
                self.added_unfinished = True
                if self.is_slave:
                    self.server.notify_master("/database/add_unfinished?url="
                                              + urllib.parse.quote(path)
                                              + "&name=" + urllib.parse.quote(self.player.title)
                                              + "&length=" + str(self.player.get_length())
                                              + "&time=" + str(current_time())
                                              + "&image=" + urllib.parse.quote(img)
                                              + "&type=" + watching_type)
                else:
                    self.database.add_watching_item(watching_type, self.player.title, path, self.player.img,
                                                    self.player.get_length(), current_time())

            if not self.removed_unfinished and self.player.get_position() > 10:
                # Update unfinished
                pos = self.player.get_position()
                if self.last_play_update_time != pos:
                    self.last_play_update_time = pos
                    if self.is_slave:
                        self.server.notify_master(
                            "/database/update_unfinished?url=" + urllib.parse.quote(path) + "&position=" + str(
                                pos) + "&watchedAt=" + str(current_time()))
                    else:
                        self.database.update_watching_item(path, pos, current_time())

            time.sleep(5)

    def watch_wifi(self):
        if not Settings.get_bool("show_gui"):
            return

        rasp = Settings.get_bool("raspberry")
        if rasp:
            proc = subprocess.Popen(["iwgetid"], stdout=subprocess.PIPE, universal_newlines=True)
            out, err = proc.communicate()
            network_ssid = out.split(":")[1]

        while self.running:
            if rasp:
                proc = subprocess.Popen(["iwlist", "wlan0", "scan"], stdout=subprocess.PIPE, universal_newlines=True)
                out, err = proc.communicate()
                cells = out.split("Cell ")
                cell_lines = [x for x in cells if network_ssid in x]
                for line in cell_lines.split("\n"):
                    if "Quality" in line:
                        fields = line.split("  ")
                        for field in fields:
                            field.replace(" ", "")
                            if len(field) <= 2:
                                continue

                            Logger.write(2, "Field: " + field)
                            key_value = field.split("=")
                            if len(key_value) == 1:
                                key_value = field.split(":")

                            Logger.write(2, "WIFI " + str(key_value[0]) + ": " + str(key_value[1]))
                            if key_value[0] == "Quality":
                                value_max = key_value[1].split("/")
                                self.gui.set_wifi_quality(float(value_max[0]) / float(value_max[1]) * 100)
            else:
                proc = subprocess.Popen(["Netsh", "WLAN", "show", "interfaces"], stdout=subprocess.PIPE, universal_newlines=True)
                out, err = proc.communicate()
                lines = out.split("\n")
                for line in lines:
                    if "Signal" in line:
                        split = line.split(":")
                        self.gui.set_wifi_quality(float(split[1].replace("%", "")))

            time.sleep(5)

    def init_folders(self):
        folder = Settings.get_string("base_folder")
        directory = os.path.dirname(folder) + "/" + "subs"
        if not os.path.exists(directory):
            os.makedirs(directory)

    def hook_events(self):
        self.player.on_state_change(self.player_state_change)

        EventManager.register_event(EventType.StartPlayer, self.start_player)
        EventManager.register_event(EventType.StopPlayer, self.stop_player)
        EventManager.register_event(EventType.PauseResumePlayer, self.pause_resume_player)
        EventManager.register_event(EventType.SetVolume, self.set_volume)
        EventManager.register_event(EventType.Seek, self.seek)

        EventManager.register_event(EventType.SetSubtitleFile, self.set_subtitle_file)
        EventManager.register_event(EventType.SetSubtitleId, self.set_subtitle_id)
        EventManager.register_event(EventType.SetSubtitleOffset, self.set_subtitle_offset)
        EventManager.register_event(EventType.SubtitleDownloaded, self.set_subtitle_file)
        EventManager.register_event(EventType.SetAudioId, self.set_audio_id)

        EventManager.register_event(EventType.TorrentMetadataDone, self.torrent_metadata_done)
        EventManager.register_event(EventType.StartTorrent, self.start_torrent)
        EventManager.register_event(EventType.StopTorrent, self.stop_torrent)
        EventManager.register_event(EventType.NewDHTNode, self.new_dht_node)

    def start_torrent(self, url, output_mode):
        success, torrent = Torrent.create_torrent(1, url, output_mode)
        if success:
            self.torrent = torrent
            torrent.start()
        else:
            Logger.write(2, "Invalid torrent")
            EventManager.throw_event(EventType.Error, ["torrent_error", "Invalid torrent"])
            if self.torrent is not None:
                self.torrent.stop()
                self.torrent = None

            time.sleep(1)
            self.player.stop()

    def stop_torrent(self):
        if self.torrent:
            self.torrent.stop()
            self.torrent = None

    def new_dht_node(self, ip, port):
        if self.dht_enabled:
            self.dht.add_node_by_ip_port(ip, port)

    def player_state_change(self, prev_state, new_state):
        Logger.write(2, "State change from " + str(prev_state) + " to " + str(new_state))
        EventManager.throw_event(EventType.PlayerStateChange, [prev_state, new_state])
        if new_state == PlayerState.Ended:
            if self.torrent is not None:
                self.torrent.stop()
                Logger.write(2, "Ended " + self.torrent.media_file.name)
            if self.player.type != "YouTube":
                thread = CustomThread(self.stop_player, "Stopping player")
                thread.start()

    def torrent_metadata_done(self):
        if self.torrent:
            if self.player.title == "Direct Link":
                self.player.title = self.torrent.name

    def request_dht_peers(self, torrent):
        if self.dht_enabled:
            self.dht.get_peers(torrent, self.add_peers_from_dht)

    def add_peers_from_dht(self, torrent, peers):
        torrent.peer_manager.add_potential_peers_from_ip_port(peers)

    def start_player(self, type, title, url, img=None, position=0):
        self.stop_player()
        self.player.play(type, title, url, img, position)

        self.added_unfinished = False
        self.removed_unfinished = False

    def stop_player(self):
        self.youtube_end_counter = 0
        self.player.stop()

    def pause_resume_player(self):
        self.player.pause_resume()

    def set_volume(self, vol):
        self.player.set_volume(vol)

    def seek(self, pos):
        self.player.set_time(pos)

    def set_subtitle_file(self, file):
        self.player.set_subtitle_file(file)

    def set_subtitle_id(self, id):
        self.player.set_subtitle_track(id)

    def set_subtitle_offset(self, offset):
        self.player.set_subtitle_delay(offset)

    def set_audio_id(self, track):
        self.player.set_audio_track(track)

    def stop(self):
        self.running = False

        Logger.write(3, "Stopping")
        if self.torrent is not None:
            Logger.write(3, "Stopping torrent")
            self.torrent.stop()
        if self.player is not None:
            Logger.write(3, "Stopping player")
            self.player.stop()
        if self.server is not None:
            Logger.write(3, "Stopping server")
            self.server.stop()
        if self.gui is not None:
            Logger.write(3, "Stopping gui")
            self.gui.close()

        Logger.write(3, "Stopped")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return

        filename, line, dummy, dummy = traceback.extract_tb(exc_traceback).pop()
        filename = os.path.basename(filename)

        Logger.write(3, "Unhandled exception on line " + str(line) + ", file " + filename, 'error')
        Logger.write(3, "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)), 'error')

        sys.exit(1)


try:
    StartUp()
except Exception as e:
    Logger.write(3, "Exception during startup: " + str(e))
    Logger.write(3, traceback.format_exc())
