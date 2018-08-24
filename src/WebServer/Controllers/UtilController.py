import os
import urllib.parse
import urllib.request

import psutil
from tornado import gen

from Interface.TV.VLCPlayer import PlayerState
from Shared.Events import EventManager
from Shared.Events import EventType
from Shared.Logger import Logger
from Shared.Settings import Settings as AppSettings
from Shared.Stats import Stats
from Shared.Threading import ThreadManager
from Shared.Util import to_JSON, parse_bool, RequestFactory, current_time, write_size
from MediaPlayer.Util.Enums import TorrentState
from WebServer.Models import DebugInfo, CurrentMedia, Version, Settings, Info, Status, StartUp


class UtilController:

    @staticmethod
    def player_state(start):
        state = start.gui_manager.player.state

        if not start.gui_manager.player.prepared:
            if state == PlayerState.Nothing or state == PlayerState.Ended:
                return to_JSON(CurrentMedia(0, None, None, None, None, 0, 0, 100, 0, 0, [], 0, False, [], 0, 0)).encode('utf8')

        if state == PlayerState.Nothing or state == PlayerState.Ended:
            state = PlayerState.Opening

        title = start.gui_manager.player.title
        percentage = 0
        if start.torrent_manager.torrent is not None and start.torrent_manager.torrent.media_file is not None:
            buffered = start.torrent_manager.torrent.bytes_ready_in_buffer
            percentage = buffered / start.torrent_manager.torrent.media_file.length * 100
            if start.torrent_manager.torrent.state == TorrentState.Done:
                percentage = 100

        media = CurrentMedia(state.value,
                             start.gui_manager.player.type,
                             title,
                             start.gui_manager.player.path,
                             start.gui_manager.player.img,
                             start.gui_manager.player.get_position(),
                             start.gui_manager.player.get_length(), start.gui_manager.player.get_volume(),
                             start.gui_manager.player.get_length(), start.gui_manager.player.get_selected_sub(),
                             start.gui_manager.player.get_subtitle_tracks(),
                             start.gui_manager.player.get_subtitle_delay() / 1000 / 1000,
                             True,
                             start.gui_manager.player.get_audio_tracks(),
                             start.gui_manager.player.get_audio_track(),
                             percentage)
        return to_JSON(media)

    @staticmethod
    def debug(start):
        torrent = start.torrent_manager.torrent
        if torrent is None:
            de = DebugInfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ThreadManager.thread_count(), psutil.cpu_percent(), psutil.virtual_memory().percent, 0, 0)
        else:
            de = DebugInfo(len(torrent.peer_manager.potential_peers),
                           len(torrent.peer_manager.connected_peers),
                           torrent.total_size,
                           torrent.download_counter.total,
                           torrent.download_counter.value,
                           torrent.bytes_ready_in_buffer,
                           torrent.bytes_total_in_buffer,
                           torrent.bytes_streamed,
                           torrent.state,
                           torrent.stream_position,
                           torrent.stream_buffer_position,
                           ThreadManager.thread_count(),
                           psutil.cpu_percent(),
                           psutil.virtual_memory().percent,
                           torrent.left,
                           torrent.overhead)

        if AppSettings.get_bool("dht"):
            de.add_dht(start.torrent_manager.dht.routing_table.count_nodes())

        return to_JSON(de)

    @staticmethod
    def status(start):
        speed = -1
        ready = -1
        torrent_state = -1
        connected_peers = -1
        potential_peers = -1
        if start.torrent_manager.torrent:
            speed = write_size(start.torrent_manager.torrent.download_counter.value)
            ready = start.torrent_manager.torrent.bytes_ready_in_buffer
            torrent_state = start.torrent_manager.torrent.state
            connected_peers = len(start.torrent_manager.torrent.peer_manager.connected_peers)
            potential_peers = len(start.torrent_manager.torrent.peer_manager.potential_peers)

        return to_JSON(Status(speed, ready, psutil.cpu_percent(), psutil.virtual_memory().percent, torrent_state, connected_peers, potential_peers))

    @staticmethod
    def info():
        info = Info(current_time() - Stats['start_time'].total, Stats['peers_connect_try'].total, Stats['peers_connect_failed'].total, Stats['peers_connect_success'].total,
                    Stats['peers_source_dht'].total, Stats['peers_source_udp_tracker'].total, Stats['peers_source_http_tracker'].total, Stats['peers_source_exchange'].total,
                    write_size(Stats['total_downloaded'].total), Stats['threads_started'].total, Stats['subs_downloaded'].total, Stats['vlc_played'].total,
                    write_size(Stats['max_download_speed'].total))

        return to_JSON(info)

    @staticmethod
    def version(start):
        return to_JSON(Version(start.version))

    @staticmethod
    @gen.coroutine
    def get_protected_img(url):
        try:
            result = yield RequestFactory.make_request_async(url)
            if not result:
                Logger.write(2, "Couldnt get image: " + urllib.parse.unquote(url))
                result = open(os.getcwd() + "/Interface/Mobile/Images/unknown.png", "rb").read()
        except Exception:
            result = open(os.getcwd() + "/Interface/Mobile/Images/noimage.png", "rb").read()
        return result

    @staticmethod
    def get_settings():
        set = Settings(AppSettings.get_bool("raspberry"),
                       AppSettings.get_bool("show_gui"),
                       AppSettings.get_bool("use_external_trackers"),
                       AppSettings.get_int("max_subtitles_files"))
        return to_JSON(set)

    @staticmethod
    def save_settings(raspberry, gui, external_trackers, max_subs):
        Logger.write(2, 'Saving new settings')

        AppSettings.set_setting("raspberry", parse_bool(raspberry))
        AppSettings.set_setting("show_gui", parse_bool(gui))
        AppSettings.set_setting("use_external_trackers", parse_bool(external_trackers))
        AppSettings.set_setting("max_subtitles_files", int(max_subs))

    @staticmethod
    def test():
        Logger.write(2, "============== Test ===============")
        EventManager.throw_event(EventType.Log, [])
        with Logger.lock:
            Logger.write(3, "-- Threads --")
            for thread in ThreadManager.threads:
                Logger.write(3, "     " + thread.thread_name + ", running for " + str((current_time() - thread.start_time)/1000) + " seconds")

    @staticmethod
    def shutdown():
        Logger.write(3, "Shutdown")
        os.system('sudo shutdown now')

    @staticmethod
    def restart_pi():
        Logger.write(3, "Restart")
        os.system('sudo reboot')

    @staticmethod
    def startup():
        return to_JSON(StartUp(AppSettings.get_string("name")))