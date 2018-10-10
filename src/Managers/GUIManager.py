import json
import os
import sys
import urllib.parse

from Interface.TV.GUI import GUI
from Interface.TV.VLCPlayer import VLCPlayer, PlayerState
from Managers.TorrentManager import TorrentManager
from MediaPlayer.Util.Util import try_parse_season_episode, is_media_file
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import RequestFactory, Singleton
from WebServer.Models import FileStructure
from WebServer.TornadoServer import TornadoServer


class GUIManager(metaclass=Singleton):

    def __init__(self):
        self.gui = None
        self.app = None
        self.player = VLCPlayer()
        self.youtube_end_counter = 0
        self.next_episode_manager = NextEpisodeManager(self)

        self.player.on_state_change(self.player_state_change)
        self.player.on_player_stopped(self.player_stopped)

        EventManager.register_event(EventType.PreparePlayer, self.prepare_player)
        EventManager.register_event(EventType.StartPlayer, self.start_player)
        EventManager.register_event(EventType.PlayerStateChange, self.player_state_changed)
        EventManager.register_event(EventType.StartTorrent, self.reset_next_episode)
        EventManager.register_event(EventType.TorrentMediaFileSelection, self.user_file_selected)

        EventManager.register_event(EventType.StopPlayer, self.stop_player)
        EventManager.register_event(EventType.PauseResumePlayer, self.pause_resume_player)
        EventManager.register_event(EventType.SetVolume, self.set_volume)
        EventManager.register_event(EventType.Seek, self.seek)

        EventManager.register_event(EventType.TorrentMediaFileSet, self.torrent_media_file_set)

        EventManager.register_event(EventType.SetSubtitleFile, self.set_subtitle_file)
        EventManager.register_event(EventType.SetSubtitleId, self.set_subtitle_id)
        EventManager.register_event(EventType.SetSubtitleOffset, self.set_subtitle_offset)
        EventManager.register_event(EventType.SubtitleDownloaded, self.set_subtitle_file)
        EventManager.register_event(EventType.SetAudioId, self.set_audio_id)

        EventManager.register_event(EventType.NoPeers, self.no_peers)

    def start_gui(self):
        self.app, self.gui = GUI.new_gui(self)

        if self.gui is not None:
            self.gui.showFullScreen()
            sys.exit(self.app.exec_())

    def no_peers(self):
        self.player.stop()
        self.next_episode_manager.reset()

    def player_state_change(self, prev_state, new_state):
        Logger.write(2, "State change from " + str(prev_state) + " to " + str(new_state))
        EventManager.throw_event(EventType.PlayerStateChange, [prev_state, new_state])

        if new_state == PlayerState.Ended:
            if self.player.type != "YouTube":
                thread = CustomThread(self.stop_player, "Stopping player")
                thread.start()

    def user_file_selected(self, path):
        self.player.title = os.path.basename(path)

    def reset_next_episode(self, url, file):
        self.next_episode_manager.reset()

    def player_stopped(self, position, length):
        if not length:
            return

        factor = float(position)/float(length)
        if length - position < 60 and length != position and factor > 0.9:
            self.check_next_episode()

    def player_state_changed(self, old, new):
        if new != PlayerState.Ended:
            return

        self.check_next_episode()

    def check_next_episode(self):
        if self.next_episode_manager.next_type is not None:
            Logger.write(2, "Continuing next episode: " + self.next_episode_manager.next_title)
            EventManager.throw_event(EventType.NextEpisodeSelection, [self.next_episode_manager.next_path,
                                                                      self.next_episode_manager.next_title,
                                                                      self.next_episode_manager.next_season,
                                                                      self.next_episode_manager.next_episode,
                                                                      self.next_episode_manager.next_type,
                                                                      self.next_episode_manager.next_media_file,
                                                                      self.next_episode_manager.next_img])

    def prepare_player(self, type, title, url, img, position, media_file):
        self.player.prepare_play(type, title, url, img, position, media_file)

    def start_player(self):
        if self.player.type == "YouTube":
            self.next_episode_manager.reset()

        self.player.play()

    def torrent_media_file_set(self):
        self.player.play(0, TorrentManager().torrent.media_file.name)
        self.next_episode_manager.check_next_episode()

    def start_torrent(self, url):
        self.player.stop()

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


class NextEpisodeManager:

    def __init__(self, gui_manager):
        self.gui_manager = gui_manager
        EventManager.register_event(EventType.StartPlayer, self.check_next_episode)

        self.next_type = None
        self.next_path = None
        self.next_title = None
        self.next_media_file = None
        self.next_img = None
        self.next_season = 0
        self.next_episode = 0

    def reset(self):
        self.next_img = None
        self.next_type = None
        self.next_path = None
        self.next_title = None
        self.next_media_file = None
        self.next_season = 0
        self.next_episode = 0

    def check_next_episode(self):
        if self.gui_manager.player.type == "File":
            self.reset()
            # Try to get next episode from same folder
            season, epi = try_parse_season_episode(self.gui_manager.player.path)
            if season == 0 or epi == 0:
                Logger.write(2, "No next episode of file, season/epi not parsed")
                return

            if Settings.get_bool("slave"):
                index = self.gui_manager.player.path.index("/file/")
                dir_name = os.path.dirname(self.gui_manager.player.path[index + 6:])
                data = TornadoServer.request_master("/hd/directory?path=" + dir_name)
                result = json.loads(data.decode("utf8"))
                file_list = result["files"]
            else:
                dir_name = os.path.dirname(self.gui_manager.player.path)
                file_list = FileStructure(dir_name).files

            for potential in file_list:
                if not is_media_file(potential):
                    continue

                s, e = try_parse_season_episode(potential)
                if s == season and e == epi + 1:
                    Logger.write(2, "Found next episode: " + potential)
                    self.next_season = s
                    self.next_episode = epi + 1
                    self.next_type = "File"
                    self.next_title = potential
                    self.next_path = dir_name + "/" + potential
                    return
            Logger.write(2, "No next episode of file, no matching next season/epi found in file list")

        elif self.gui_manager.player.type != "Radio" and self.gui_manager.player.type != "YouTube" and self.gui_manager.player.type != "Image":
            season, epi = try_parse_season_episode(TorrentManager().torrent.media_file.path)
            if season == 0 or epi == 0:
                Logger.write(2, "No next episode found, season/epi not parsed")
                return

            # Try to get next episode from same torrent
            for file in TorrentManager().torrent.files:
                if not is_media_file(file.path):
                    continue

                s, e = try_parse_season_episode(file.path)
                if s == season and e == epi + 1:
                    Logger.write(2, "Found next episode: " + file.path)
                    self.next_season = s
                    self.next_episode = epi + 1
                    self.next_type = "Torrent"
                    self.next_title = self.gui_manager.player.title.replace("E" + self.add_leading_zero(epi), "E" + self.add_leading_zero(epi + 1))
                    self.next_path = TorrentManager().torrent.uri
                    self.next_media_file = file.name
                    break

            if self.next_type is None:
                #  Try to get next episode from shows list
                season, epi = try_parse_season_episode(self.gui_manager.player.title)
                if season == 0 or epi == 0:
                    Logger.write(2, "No next episode of show, season/epi not parsed")
                    return

                show = self.gui_manager.player.title[8:]
                results = json.loads(RequestFactory.make_request("http://127.0.0.1/shows/get_shows?page=1&orderby=trending&keywords=" + urllib.parse.quote(show)).decode('utf8'))
                if len(results) == 0:
                    Logger.write(2, "No next episode of show, request returned no results for shows")
                    return

                show = json.loads(RequestFactory.make_request("http://127.0.0.1/shows/get_show?id=" + urllib.parse.quote(results[0]["_id"])).decode('utf8'))
                next_epi = [x for x in show["episodes"] if x["season"] == season and x["episode"] == epi + 1]
                if len(next_epi) == 0:
                    Logger.write(2, "No next episode of show, request returned no results for next epi")
                    return

                Logger.write(2, "Found next episode: " + next_epi[0]["title"])
                self.next_season = season
                self.next_episode = epi + 1
                self.next_type = "Torrent"
                self.next_title = self.gui_manager.player.title.replace("E" + self.add_leading_zero(epi), "E" + self.add_leading_zero(epi + 1))
                self.next_path = next_epi[0]["torrents"]["0"]["url"]
                self.next_img = self.gui_manager.player.img

    def add_leading_zero(self, val):
        i = int(val)
        if i < 10:
            return "0" + str(i)
        return str(i)

