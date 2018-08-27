import os
import sys

from Interface.TV.GUI import GUI
from Interface.TV.VLCPlayer import VLCPlayer, PlayerState
from MediaPlayer.Util.Util import try_parse_season_episode, is_media_file
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Threading import CustomThread
from WebServer.Models import FileStructure


class GUIManager:

    def __init__(self, program):
        self.program = program
        self.gui = None
        self.app = None
        self.player = VLCPlayer()
        self.youtube_end_counter = 0

        self.player.on_state_change(self.player_state_change)

        EventManager.register_event(EventType.PreparePlayer, self.prepare_player)
        EventManager.register_event(EventType.StartPlayer, self.start_player)
        EventManager.register_event(EventType.PlayerStateChange, self.check_next_episode)

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

    def check_next_episode(self, old, new):
        if new != PlayerState.Nothing:
            return

        playing_type = self.player.type
        path = self.player.path

        if playing_type == "File":
            season, epi = try_parse_season_episode(path)
            if season == 0 or epi == 0:
                return

            dir_name = os.path.dirname(path)
            for potential in FileStructure(dir_name).files:
                if not is_media_file(potential):
                    continue

                s, e = try_parse_season_episode(potential)
                if s == season and e == epi + 1:
                    Logger.write(2, "Found next episode: " + potential)
                    EventManager.throw_event(EventType.NextEpisodeSelection, [dir_name + "/" + potential, potential, s, e, "File"])
                    break

        else:
            pass

    def prepare_player(self, type, title, url, img, position, media_file):
        self.player.prepare_play(type, title, url, img, position, media_file)

    def start_player(self):
        self.player.play()

    def torrent_media_file_set(self):
        self.player.play(0, self.program.torrent_manager.torrent.media_file.name)

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