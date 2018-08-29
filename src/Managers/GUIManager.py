import json
import os
import sys

from Interface.TV.GUI import GUI
from Interface.TV.VLCPlayer import VLCPlayer, PlayerState
from MediaPlayer.Util.Util import try_parse_season_episode, is_media_file
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import RequestFactory
from WebServer.Models import FileStructure


class GUIManager:

    def __init__(self, program):
        self.program = program
        self.gui = None
        self.app = None
        self.player = VLCPlayer()
        self.youtube_end_counter = 0
        self.next_episode_manager = NextEpisodeManager(self)

        self.player.on_state_change(self.player_state_change)

        EventManager.register_event(EventType.PreparePlayer, self.prepare_player)
        EventManager.register_event(EventType.StartPlayer, self.start_player)
        EventManager.register_event(EventType.PlayerStateChange, self.check_next_episode)
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

    def start_gui(self):
        self.app, self.gui = GUI.new_gui(self.program)

        if self.gui is not None:
            self.gui.showFullScreen()
            sys.exit(self.app.exec_())

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

    def check_next_episode(self, old, new):
        if new != PlayerState.Ended:
            return

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
        self.player.play()

    def torrent_media_file_set(self):
        self.player.play(0, self.program.torrent_manager.torrent.media_file.name)
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
        EventManager.register_event(EventType.SetNextEpisode, self.set_next_episode_url)

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

    def set_next_episode_url(self, season, episode, url):
        self.next_season = season
        self.next_episode = episode
        self.next_type = "Torrent"
        self.next_img = self.gui_manager.player.img
        self.next_title = self.gui_manager.player.title.replace("E" + self.add_leading_zero(int(episode) - 1), "E" + self.add_leading_zero(episode))
        self.next_path = url
        Logger.write(2, "Set next episode: " + self.next_title)

    def check_next_episode(self):
        if self.gui_manager.player.type == "File":
            self.reset()
            season, epi = try_parse_season_episode(self.gui_manager.player.path)
            if season == 0 or epi == 0:
                return

            if Settings.get_bool("slave"):
                index = self.gui_manager.player.path.index("/file/")
                dir_name = os.path.dirname(self.gui_manager.player.path[index + 6:])
                result = json.loads(RequestFactory.make_request(str(Settings.get_string("master_ip") + "/hd/directory?path=" + dir_name)).decode())
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
                    break

        elif self.gui_manager.player.type != "YouTube" and self.gui_manager.player.type != "Image":
            if self.next_type is not None:
                return # already have next epi

            season, epi = try_parse_season_episode(self.gui_manager.program.torrent_manager.torrent.media_file.path)
            if season == 0 or epi == 0:
                return

            for file in self.gui_manager.program.torrent_manager.torrent.files:
                if not is_media_file(file.path):
                    continue

                s, e = try_parse_season_episode(file.path)
                if s == season and e == epi + 1:
                    Logger.write(2, "Found next episode: " + file.path)
                    self.next_season = s
                    self.next_episode = epi + 1
                    self.next_type = "Torrent"
                    self.next_title = self.gui_manager.player.title.replace("E" + self.add_leading_zero(epi), "E" + self.add_leading_zero(epi + 1))
                    self.next_path = self.gui_manager.program.torrent_manager.torrent.uri
                    self.next_media_file = file.name
                    break

    def add_leading_zero(self, val):
        i = int(val)
        if i < 10:
            return "0" + str(i)
        return str(i)

