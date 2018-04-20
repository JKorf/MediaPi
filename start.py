#!/usr/bin/env python3
import json
import os
import cProfile
import urllib.parse

from shutil import copytree, rmtree

os.chdir(os.path.dirname(__file__))

from Database.Database import Database
from TorrentSrc.Streaming.StreamListener import StreamListener

from TorrentSrc.TorrentManager import TorrentManager
from TorrentSrc.Util.Stats import PyStats

from DHT.DHTEngine import DHTEngine

from Shared.Util import current_time
from Shared.Events import EventManager, EventType
from Shared.Stats import Stats
from Shared.Logger import Logger
from Shared.Settings import Settings

from TorrentSrc.Util.Threading import CustomThread

from Web.Server.TornadoServer import TornadoServer
from Web.Server.Subtitles import SubtitleProvider
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
        Stats['start_time'].add(current_time())
        self.gui = None
        self.app = None
        self.player = None
        self.server = None
        self.torrent_manager = TorrentManager()
        self.stream_torrent = None
        self.running = True
        self.youtube_end_counter = 0
        self.is_slave = Settings.get_bool("slave")

        self.added_unfinished = False
        self.removed_unfinished = False

        sys.excepthook = self.handle_exception

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
        self.start_stat_observer()
        self.init_player()
        self.init_sound()
        self.subtitle_provider = SubtitleProvider(self)
        self.start_subtitle_provider()
        self.init_folders()

        version = json.loads(UtilController.version())
        Logger.write(3, "MediaPlayer version " + version['version_number'] + " (" + version['build_date'] + ")")
        Logger.write(3, "Slave: " + str(self.is_slave))
        if self.is_slave:
            Logger.write(3, "Master ip: " + str(Settings.get_string("master_ip")))
        Logger.write(3, "Pi: " + str(Settings.get_bool("raspberry")))

        if self.gui is not None:
            self.gui.showFullScreen()
            sys.exit(self.app.exec_())
        else:
            while self.running:
                time.sleep(1)

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

    def start_subtitle_provider(self):
        thread = CustomThread(self.subtitle_provider.update, "Subtitle loop")
        thread.start()

    def start_gui(self):
        self.app, self.gui = GUI.new_gui(self)

    def start_stat_observer(self):
        thread = CustomThread(self.watch_stats, "Watch playing")
        thread.start()

    def watch_stats(self):
        while self.running:
            if self.stream_torrent is not None:
                # Check max download speed
                current = Stats['max_download_speed'].total
                for torrent in self.torrent_manager.torrents:
                    if torrent.download_counter.max > current:
                        Stats['max_download_speed'].set(torrent.download_counter.max)

                # Update time for resuming
                if self.player.get_position() > 0 and self.player.get_length() - self.player.get_position() < 30:
                    if self.added_unfinished and not self.removed_unfinished:
                        self.removed_unfinished = True
                        if self.is_slave:
                            self.server.notify_master("/database/remove_unfinished?url=" + urllib.parse.quote(self.stream_torrent.uri))
                        else:
                            self.database.remove_watching_torrent(self.stream_torrent.uri)
                elif self.player.get_position() > 10 and not self.added_unfinished:
                    self.added_unfinished = True
                    if self.is_slave:
                        self.server.notify_master("/database/add_unfinished?url="
                                                  + urllib.parse.quote(self.stream_torrent.uri)
                                                  + "&name=" + urllib.parse.quote(self.player.title)
                                                  + "&length=" + str(self.player.get_length())
                                                  + "&time=" + str(current_time())
                                                  + "&image=" + urllib.parse.quote(self.player.img))
                    else:
                        self.database.add_watching_torrent(self.player.title, self.stream_torrent.uri, self.player.img,
                                                       self.player.get_length(), current_time())
                elif self.player.get_position() > 10:
                    if self.is_slave:
                        self.server.notify_master("/database/update_unfinished?url=" + urllib.parse.quote(self.stream_torrent.uri) + "&position=" + str(self.player.get_position()))
                    else:
                        self.database.update_watching_torrent(self.stream_torrent.uri, self.player.get_position())

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

        EventManager.register_event(EventType.InvalidTorrent, self.invalid_torrent)
        EventManager.register_event(EventType.StreamTorrentStarted, self.stream_torrent_started)
        EventManager.register_event(EventType.StreamTorrentStopped, self.stream_torrent_stopped)
        EventManager.register_event(EventType.TorrentMetadataDone, self.torrent_metadata_done)

        EventManager.register_event(EventType.NewDHTNode, self.new_dht_node)

    def new_dht_node(self, ip, port):
        if self.dht_enabled:
            self.dht.add_node_by_ip_port(ip, port)

    def player_state_change(self, prev_state, new_state):
        Logger.write(2, "State change from " + str(prev_state) + " to " + str(new_state))
        EventManager.throw_event(EventType.PlayerStateChange, [prev_state, new_state])
        if new_state == PlayerState.Ended:
            if self.stream_torrent is not None:
                Logger.write(2, "Ended " + self.stream_torrent.media_file.name)
                self.torrent_manager.remove_torrent(self.stream_torrent.id)
            if self.player.type != "YouTube":
                thread = CustomThread(self.stop_player, "Stopping player")
                thread.start()

    def torrent_metadata_done(self, torrent):
        if self.stream_torrent and torrent.id == self.stream_torrent.id:
            if self.player.title == "Direct Link":
                self.player.title = torrent.name

    def stream_torrent_stopped(self, torrent):
        self.stream_torrent = None
        self.stop_player()

    def stream_torrent_started(self, torrent):
        self.added_unfinished = False
        self.removed_unfinished = False
        self.stream_torrent = torrent

    def request_dht_peers(self, torrent):
        if self.dht_enabled:
            self.dht.get_peers(torrent, self.add_peers_from_dht)

    def add_peers_from_dht(self, torrent, peers):
        torrent.peer_manager.add_potential_peers_from_ip_port(peers)

    def invalid_torrent(self, reason):
        Logger.write(2, "Invalid torrent")
        EventManager.throw_event(EventType.Error, ["torrent_error", "Invalid torrent: " + reason])
        if self.stream_torrent is not None:
            self.stream_torrent.stop()
            self.stream_torrent = None

        time.sleep(1)
        self.player.stop()

    def start_player(self, type, title, url, img=None, position=0):
        self.stop_player()
        self.player.play(type, title, url, img, position)

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
        if self.stream_torrent is not None:
            Logger.write(3, "Stopping torrent")
            self.stream_torrent.stop()
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


current_dir = os.path.dirname(__file__)
if "pi_update_" in current_dir:
    Logger.write(2, "Update: Copying update back to main folder")
    base_folder = Settings.get_string("base_folder")

    try:
        if os.path.exists(base_folder):
            rmtree(base_folder)
        copytree(current_dir, base_folder)
    except Exception as e:
        Logger.write(3, "Updating failed; couldn't copy back: " + str(e))

    Logger.write(3, "Update: Copying update to main folder completed, restarting from main directory")
    python = sys.executable
    os.execl(python, python, base_folder + "/start.py")
else:
    stats = cProfile.Profile()
    stats.enable()
    try:
        StartUp()
    except Exception as e:
        Logger.write(3, "Exception during startup: " + str(e))
        Logger.write(3, traceback.format_exc())
    finally:
        stats.disable()
        PyStats.add_stats(stats)
        PyStats.stats.dump_stats('test.txt')
