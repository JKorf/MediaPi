import datetime
import os
import time
from enum import Enum

from MediaPlayer.Player import vlc
from MediaPlayer.Player.vlc import libvlc_get_version, EventType as VLCEventType, MediaSlaveType, MediaSlave, Media
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import Singleton


class VLCPlayer(metaclass=Singleton):

    def __init__(self):
        self.__vlc_instance = None
        self.player_state = PlayerData()

        self.instantiate_vlc()

        self.media = None
        self.__player = self.__vlc_instance.media_player_new()
        if Settings.get_bool("raspberry"):
            self.__player.set_fullscreen(True)

        self.__event_manager = self.__player.event_manager()
        self.hook_events()

        self.set_volume(75)

        self.trying_subitems = False

        EventManager.register_event(EventType.SetSubtitleFiles, self.set_subtitle_files)
        EventManager.register_event(EventType.StopPlayer, self.stop)
        EventManager.register_event(EventType.NoPeers, self.stop)

        self.player_observer = CustomThread(self.observe_player, "Player observer")
        self.player_observer.start()

    def instantiate_vlc(self):
        parameters = self.get_instance_parameters()
        Logger().write(2, "VLC parameters: " + str(parameters))
        self.__vlc_instance = vlc.Instance("cvlc", *parameters)
        Logger().write(3, "VLC version " + libvlc_get_version().decode('utf8'))

    def play(self, url, time=0):
        parameters = self.get_play_parameters(url, time)

        Logger().write(2, "VLC Play | Url: " + url)
        Logger().write(2, "VLC Play | Time: " + str(time))
        Logger().write(2, "VLC Play | Parameters: " + str(parameters))

        self.player_state.start_update()
        self.player_state.path = url
        self.player_state.stop_update()

        self.media = Media(url, *parameters)
        self.__player.set_media(self.media)
        self.__player.play()

    @staticmethod
    def get_instance_parameters():
        params = ["--verbose=" + str(Settings.get_int("vlc_log_level")),
                  "--network-caching=" + str(Settings.get_int("network_caching")),
                  "--ipv4-timeout=500",
                  "--image-duration=-1"]

        if Settings.get_bool("raspberry"):
            log_path = Settings.get_string("base_folder") + "/Logs"
            params.append("--logfile=" + log_path + '/vlclog_' + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".txt")
            params.append("--file-logging")
            params.append("--file-caching=5000")

        return params

    def get_play_parameters(self, url, time):
        params = []
        if time != 0:
            params.append("start-time=" + str(time // 1000))

        return params

    def pause_resume(self):
        self.__player.pause()

    def stop(self):
        self.__player.stop()

    def mute_on(self):
        self.__player.audio_set_mute(True)

    def mute_off(self):
        self.__player.audio_set_mute(False)

    def set_volume(self, vol):
        self.__player.audio_set_volume(vol)
        self.player_state.start_update()
        self.player_state.volume = vol
        self.player_state.stop_update()

    def get_volume(self):
        return self.__player.audio_get_volume()

    def get_position(self):
        return int(self.__player.get_time() / 1000)

    def get_length(self):
        return int(self.__player.get_length())

    def get_length_ms(self):
        return int(self.__player.get_length())

    def set_time(self, pos):
        self.__player.set_time(pos)
        self.player_state.start_update()
        self.player_state.playing_for = pos
        self.player_state.stop_update()

    def set_position(self, pos):
        self.__player.set_position(pos)

    def set_subtitle_delay(self, delay):
        self.__player.video_set_spu_delay(delay)
        self.player_state.start_update()
        self.player_state.sub_delay = delay
        self.player_state.stop_update()

    def get_state(self):
        return self.__player.get_state()

    def get_audio_track(self):
        return self.__player.audio_get_track()

    def set_audio_track(self, track_id):
        self.__player.audio_set_track(track_id)
        self.player_state.start_update()
        self.player_state.audio_track = track_id
        self.player_state.stop_update()

    def get_audio_tracks(self):
        tracks = self.__player.audio_get_track_description()
        result = []
        for trackid, trackname in tracks:
            result.append((trackid, trackname.decode('utf8')))
        return result

    def set_subtitle_files(self, files):
        Logger().write(2, "Adding " + str(len(files)) + " subtitle files")
        pi = Settings.get_bool("raspberry")
        for file in reversed(files):
            if not pi and file[1] != ":":
                file = "C:" + file
            file = file.replace("/", os.sep).replace("\\", os.sep)
            # NOTE this must be called after Play()
            self.__player.video_set_subtitle_file(file)

    def set_subtitle_track(self, id):
        self.__player.video_set_spu(id)
        self.player_state.start_update()
        self.player_state.sub_track = id
        self.player_state.stop_update()

    def get_subtitle_count(self):
        return self.__player.video_get_spu_count()

    def get_subtitle_tracks(self):
        tracks = self.__player.video_get_spu_description()
        result = []
        for trackid, trackname in tracks:
            result.append((trackid, trackname.decode('utf-8')))
        return result

    def get_subtitle_delay(self):
        return self.__player.video_get_spu_delay()

    def get_selected_sub(self):
        return self.__player.video_get_spu()

    def hook_events(self):
        self.__event_manager.event_attach(VLCEventType.MediaPlayerOpening, self.state_change_opening)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerPlaying, self.state_change_playing)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerPaused, self.state_change_paused)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerStopped, self.state_change_stopped)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerEndReached, self.state_change_end_reached)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerEncounteredError, self.on_error)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerTimeChanged, self.on_time_change)

    def on_time_change(self, event):
        self.player_state.start_update()
        self.player_state.playing_for = event.u.new_time
        self.player_state.stop_update()

    def state_change_opening(self, event):
        if self.player_state.state != PlayerState.Opening:
            self.change_state(PlayerState.Opening)

    def state_change_playing(self, event):
        if self.player_state.state != PlayerState.Paused:
            self.player_state.length = self.get_length()
        self.change_state(PlayerState.Playing)

    def state_change_paused(self, event):
        if self.player_state.state != PlayerState.Paused:
            self.change_state(PlayerState.Paused)

    def state_change_stopped(self, event):
        if self.player_state.state != PlayerState.Nothing:
            self.change_state(PlayerState.Nothing)

            self.player_state.start_update()
            self.player_state.length = 0
            self.player_state.playing_for = 0
            self.player_state.path = None
            self.player_state.sub_delay = 0
            self.player_state.sub_track = 0
            self.player_state.sub_tracks = []
            self.player_state.audio_track = 0
            self.player_state.audio_tracks = []
            self.player_state.stop_update()

    def state_change_end_reached(self, event):
        if self.player_state.path is not None and "youtube" in self.player_state.path and not self.trying_subitems:
            Logger().write(2, "Trying youtube sub items")
            self.trying_subitems = True
            thread = CustomThread(self.try_play_subitem, "Try play subitem")
            thread.start()
        elif self.trying_subitems:
            self.trying_subitems = False

        if self.player_state.state != PlayerState.Ended:
            self.change_state(PlayerState.Ended)

    def on_error(self, event):
        Logger().write(2, "VLC error")

    def try_play_subitem(self):
        media = self.__player.get_media()
        if media is None:
            self.stop()
            return

        subs = media.subitems()
        if subs is None:
            self.stop()
            return

        if len(subs) == 1:
            subs[0].add_options("demux=avformat")
            self.__player.set_media(subs[0])
            self.__player.play()

    def change_state(self, new):
        self.player_state.start_update()
        self.player_state.state = new
        self.player_state.stop_update()

        if new == PlayerState.Ended:
            thread = CustomThread(self.stop, "Stopping player")
            thread.start()

    def observe_player(self):
        while True:
            if self.player_state.state == PlayerState.Nothing:
                time.sleep(0.5)
                continue

            self.player_state.start_update()
            self.player_state.audio_tracks = self.get_audio_tracks()
            self.player_state.audio_track = self.get_audio_track()
            self.player_state.sub_delay = self.get_subtitle_delay()
            self.player_state.sub_track = self.get_selected_sub()
            self.player_state.sub_tracks = self.get_subtitle_tracks()
            self.player_state.volume = self.get_volume()
            self.player_state.stop_update()

            time.sleep(0.5)


class PlayerState(Enum):
    Nothing = 0
    Opening = 1
    Buffering = 2
    Playing = 3
    Paused = 4
    Ended = 5


class PlayerData(Observable):

    def __init__(self):
        super().__init__("PlayerData", 0.5)

        self.path = None
        self.state = PlayerState.Nothing
        self.playing_for = 0
        self.length = 0
        self.volume = 0
        self.sub_delay = 0
        self.sub_track = 0
        self.sub_tracks = []
        self.audio_track = 0
        self.audio_tracks = []

