import os
import sys
import urllib.parse
import urllib.request

from shutil import copyfile, copytree, rmtree

import psutil
from tornado import gen

from Shared.Settings import Settings as AppSettings
from Shared.Logger import Logger
from Shared.Stats import Stats
from Shared.Util import to_JSON, parse_bool, RequestFactory, current_time
from TorrentSrc.Util.Threading import ThreadManager
from TorrentSrc.Util.Util import write_size
from Web.Server.Models import DebugInfo, current_media, Version, Settings, Info, Status, StartUp

from TorrentSrc.Util.Enums import TorrentState

from Shared.Events import EventManager

from Shared.Events import EventType


class UtilController:

    @staticmethod
    def player_state(start):
        ret = [0, 5, 6]
        if start.player is None or start.player.get_state().value in ret:
            return to_JSON(current_media(0, None, None, None, None, 0, 0, 100, 0, 0, [], 0, False, [], 0, 0)).encode('ascii')

        title = start.player.title
        percentage = 0
        if start.stream_torrent is not None and start.stream_torrent.media_file is not None:
            buffered = start.stream_torrent.bytes_ready_in_buffer
            percentage = buffered / start.stream_torrent.media_file.length * 100
            if start.stream_torrent.state == TorrentState.Done:
                percentage = 100

        media = current_media(start.player.state.value,
                              start.player.type,
                              title,
                              start.player.path,
                              start.player.img,
                              start.player.get_position(),
                              start.player.get_length(), start.player.get_volume(),
                              start.player.get_length(), start.player.get_selected_sub(),
                              start.player.get_subtitle_tracks(),
                              start.player.get_subtitle_delay() / 1000 / 1000,
                              start.subtitle_provider.is_done,
                              start.player.get_audio_tracks(),
                              start.player.get_audio_track(),
                              percentage)
        return to_JSON(media)

    @staticmethod
    def debug(start):
        torrent = None
        if len(start.torrent_manager.torrents) > 0:
            torrent = start.torrent_manager.torrents[0]
        if torrent is None:
            de = DebugInfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ThreadManager.thread_count(), psutil.cpu_percent(), psutil.virtual_memory().percent, 0)
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
                           torrent.left)

        if AppSettings.get_bool("dht"):
            de.add_dht(start.dht.routing_table.count_nodes())

        return to_JSON(de)

    @staticmethod
    def status(start):
        return to_JSON(Status(write_size(start.torrent_manager.total_speed), start.torrent_manager.stream_buffer_ready, psutil.cpu_percent(), psutil.virtual_memory().percent))

    @staticmethod
    def info():
        info = Info(current_time() - Stats['start_time'].total, Stats['peers_connect_try'].total, Stats['peers_connect_failed'].total, Stats['peers_connect_success'].total,
                    Stats['peers_source_dht'].total, Stats['peers_source_udp_tracker'].total, Stats['peers_source_http_tracker'].total, Stats['peers_source_exchange'].total,
                    write_size(Stats['total_downloaded'].total), Stats['threads_started'].total, Stats['subs_downloaded'].total, Stats['vlc_played'].total,
                    write_size(Stats['max_download_speed'].total))

        return to_JSON(info)

    @staticmethod
    def version():
        return to_JSON(Version("10/04/2017", "1.6.5"))

    @staticmethod
    @gen.coroutine
    def get_protected_img(url):
        result = yield RequestFactory.make_request_async(url)
        if not result:
            Logger.write(2, "Couldnt get image: " + urllib.parse.unquote(url))
            result = open(os.getcwd() + "/Web/Images/noimage.png", "rb").read()
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
    def test(start):
        Logger.write(2, "============== Test ===============")
        EventManager.throw_event(EventType.Log, [])

    @staticmethod
    def shutdown(start):
        Logger.write(3, "Shutdown")
        os.system('sudo shutdown now')

    @staticmethod
    def restart_pi(start):
        Logger.write(3, "Restart")
        os.system('sudo shutdown -r now')

    @staticmethod
    def restart_app():
        Logger.write(3, "Restart")
        python = sys.executable
        os.execl(python, python, *sys.argv)

    @staticmethod
    def exit(start):
        Logger.write(3, "Exit")
        start.stop()

    @staticmethod
    def startup():
        return to_JSON(StartUp(AppSettings.get_string("name")))

    @staticmethod
    def update(start):
        Logger.write(3, "Starting update")
        source_url = AppSettings.get_string("update_source")
        base_folder = AppSettings.get_string("base_folder")
        base_folder_parent = os.path.dirname(base_folder)

        try:
            if os.path.exists(base_folder_parent + "pi_update_"):
                rmtree(base_folder_parent + "pi_update_")
            copytree(source_url, base_folder_parent + "pi_update_")
        except Exception as e:
            Logger.write(3, "Update failed; Copying failed with error " + str(e))
            return
        Logger.write(3, "Copying to update folder done, restarting from new location")

        start.stop()

        python = sys.executable
        os.execl(python, python, base_folder_parent + "pi_update_/start.py")
