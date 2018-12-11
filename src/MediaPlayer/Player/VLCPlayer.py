import datetime
import os
import time
from enum import Enum

from MediaPlayer.Player import vlc
from MediaPlayer.Player.vlc import libvlc_get_version, EventType as VLCEventType
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import Singleton


class VLCPlayer(metaclass=Singleton):

    def __init__(self):
        self.__end_action = None
        self.__vlc_instance = None
        self.playerState = PlayerData()

        self.instantiate_vlc()

        self.__player = self.__vlc_instance.media_player_new()
        self.__event_manager = self.__player.event_manager()
        self.hook_events()

        self.set_volume(75)

        self.media = None
        self.prepared = False

        self.trying_subitems = False
        self.youtube_end_counter = 0

        EventManager.register_event(EventType.SetSubtitleFiles, self.set_subtitle_files)
        EventManager.register_event(EventType.SetSubtitleId, self.set_subtitle_track)
        EventManager.register_event(EventType.SetSubtitleOffset, self.set_subtitle_delay)
        EventManager.register_event(EventType.SubtitlesDownloaded, self.set_subtitle_files)
        EventManager.register_event(EventType.SetAudioId, self.set_audio_track)

        EventManager.register_event(EventType.PauseResumePlayer, self.pause_resume)
        EventManager.register_event(EventType.SetVolume, self.set_volume)
        EventManager.register_event(EventType.Seek, self.set_time)

        EventManager.register_event(EventType.PreparePlayer, self.prepare_play)
        EventManager.register_event(EventType.StartPlayer, self.play)
        EventManager.register_event(EventType.StopPlayer, self.stop)

        EventManager.register_event(EventType.TorrentMediaFileSelection, self.user_file_selected)
        EventManager.register_event(EventType.TorrentMediaFileSet, self.torrent_media_file_set)
        EventManager.register_event(EventType.NoPeers, self.stop)

        thread = CustomThread(self.watch_time_change, "VLC State watcher")
        thread.start()

    def instantiate_vlc(self):
        parameters = self.get_instance_parameters()
        Logger.write(2, "VLC parameters: " + str(parameters))
        self.__vlc_instance = vlc.Instance("vlc", *parameters)
        Logger.write(3, "VLC version " + libvlc_get_version().decode('utf8'))

    def prepare_play(self, media):
        self.media = media
        self.prepared = True

    def play(self, time=0, filename=None):
        if not self.prepared:
            raise ValueError("Player not prepared")

        if time != 0:
            self.media.start_time = time
        if filename is not None:
            self.media.file = filename

        parameters = self.get_play_parameters()

        Logger.write(2, "VLC Play | Type: " + self.media.type)
        Logger.write(2, "VLC Play | Title: " + self.media.title)
        Logger.write(2, "VLC Play | Url: " + self.media.path)
        Logger.write(2, "VLC Play | Time: " + str(self.media.start_time))
        Logger.write(2, "VLC Play | Filename: " + str(self.media.file))
        Logger.write(2, "VLC Play | Parameters: " + str(parameters))

        self.__player.set_mrl(self.media.path, *parameters)
        return self.__player.play() != -1

    @staticmethod
    def get_instance_parameters():
        params = ["--verbose=" + str(Settings.get_int("vlc_log_level")),
                  "--network-caching=" + str(Settings.get_int("network_caching")),
                  "--ipv4-timeout=500",
                  "--image-duration=-1"]

        if Settings.get_bool("raspberry"):
            log_path = Settings.get_string("log_folder")
            params.append("--logfile=" + log_path + '/vlclog_' + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".txt")
            params.append("--file-logging")
            params.append("--codec=omxil")
            params.append("--vout=omxil_vout")
            params.append("--file-caching=5000")

        return params

    def get_play_parameters(self):
        params = []
        if self.media.type == "YouTube":
            params.append("lua-intf=youtube")

        if self.media.start_time != 0:
            params.append("start-time=" + str(self.media.start_time // 1000))

        if self.media.type != "File":
            if self.media.start_time != 0 and self.media.file.endswith("mp4"):
                params.append("demux=avformat")
            elif self.media.file is not None and self.media.file.endswith("avi"):
                params.append("demux=avformat")
        return params

    def torrent_media_file_set(self, file_name):
        self.play(0, file_name)

    def user_file_selected(self, path):
        self.media.title = os.path.basename(path)

    def pause_resume(self):
        self.__player.pause()

    def stop(self):
        pos = self.get_position()
        length = self.get_length()
        self.__player.stop()
        self.media = None
        self.prepared = False
        self.youtube_end_counter = 0
        EventManager.throw_event(EventType.PlayerStopped, [pos, length])

    def fullscreen_on(self):
        self.__player.set_fullscreen(True)

    def fullscreen_off(self):
        self.__player.set_fullscreen(False)

    def mute_on(self):
        self.__player.audio_set_mute(True)

    def mute_off(self):
        self.__player.audio_set_mute(False)

    def set_volume(self, vol):
        self.__player.audio_set_volume(vol)

    def get_volume(self):
        return self.__player.audio_get_volume()

    def get_position(self):
        return int(self.__player.get_time() / 1000)

    def get_length(self):
        return int(self.__player.get_length() / 1000)

    def get_length_ms(self):
        return int(self.__player.get_length())

    def set_time(self, pos):
        self.__player.set_time(pos)

    def set_position(self, pos):
        self.__player.set_position(pos)

    def set_subtitle_delay(self, delay):
        self.__player.video_set_spu_delay(delay)

    def get_state(self):
        return self.__player.get_state()

    def get_audio_track(self):
        return self.__player.audio_get_track()

    def set_audio_track(self, track_id):
        return self.__player.audio_set_track(track_id)

    def get_audio_tracks(self):
        tracks = self.__player.audio_get_track_description()
        result = []
        for trackid, trackname in tracks:
            result.append((trackid, trackname.decode('utf8')))
        return result

    def set_subtitle_files(self, files):
        Logger.write(2, "Adding " + str(len(files)) + " subtitle files")
        pi = Settings.get_bool("raspberry")
        for file in reversed(files):
            if not pi and file[1] != ":":
                file = "C:" + file
            file = file.replace("/", os.sep).replace("\\", os.sep)
            # NOTE this must be called after Play()
            self.__player.video_set_subtitle_file(file)

    def set_subtitle_track(self, id):
        self.__player.video_set_spu(id)

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

    def get_fps(self):
        return int(1000 // (self.__player.get_fps() or 25))

    def hook_events(self):
        self.__event_manager.event_attach(VLCEventType.MediaPlayerOpening, self.state_change_opening)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerPlaying, self.state_change_playing)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerPaused, self.state_change_paused)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerStopped, self.state_change_stopped)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerEndReached, self.state_change_end_reached)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerEncounteredError, self.on_error)
        self.__event_manager.event_attach(VLCEventType.MediaPlayerTimeChanged, self.on_time_change)

    def on_time_change(self, event):
        self.playerState.playing_for = event.u.new_time
        self.playerState.updated()

    def state_change_opening(self, event):
        if self.playerState.state != PlayerState.Opening:
            self.change_state(PlayerState.Opening)

    def state_change_playing(self, event):
        if self.playerState.state == PlayerState.Paused:
            self.change_state(PlayerState.Playing)
        else:
            self.playerState.length = self.get_length()
            pass # gets handled by watching time change

    def state_change_paused(self, event):
        if self.playerState.state != PlayerState.Paused:
            self.change_state(PlayerState.Paused)

    def state_change_stopped(self, event):
        if self.playerState.state != PlayerState.Nothing:
            self.prepared = False
            self.change_state(PlayerState.Nothing)

    def state_change_end_reached(self, event):
        if self.playerState.state != PlayerState.Ended:
            if not self.trying_subitems:
                thread = CustomThread(self.stop, "Stopping player")
                thread.start()
                self.change_state(PlayerState.Ended)

    def on_error(self, event):
        self.trying_subitems = True
        thread = CustomThread(self.try_play_subitem, "Try play subitem")
        thread.start()

    def try_play_subitem(self):
        media = self.__player.get_media()
        if media is None:
            self.trying_subitems = False
            self.stop()
            return

        subs = media.subitems()
        if subs is None:
            self.trying_subitems = False
            self.stop()
            return

        if len(subs) == 1:
            subs[0].add_options("demux=avformat")
            self.__player.set_media(subs[0])
            self.__player.play()
            self.trying_subitems = False

    def watch_time_change(self):
        last_time = 0
        while True:
            this_time = self.__player.get_time()
            if this_time == 0:
                time.sleep(0.5)
                continue

            if this_time - last_time == 0:
                if self.playerState.state == PlayerState.Playing:
                    self.change_state(PlayerState.Buffering)
            else:
                if self.playerState.state == PlayerState.Buffering or self.playerState.state == PlayerState.Opening:
                    self.change_state(PlayerState.Playing)
            last_time = this_time
            time.sleep(1)

    def change_state(self, new):
        old = self.playerState.state
        self.playerState.state = new
        self.playerState.updated()

        if old == PlayerState.Opening and new == PlayerState.Playing:
            EventManager.throw_event(EventType.PlayerMediaLoaded, [self.get_length_ms()])

        Logger.write(2, "State change from " + str(old) + " to " + str(new))
        EventManager.throw_event(EventType.PlayerStateChange, [old, new])

        if new == PlayerState.Ended:
            if self.media.type != "YouTube":
                thread = CustomThread(self.stop, "Stopping player")
                thread.start()


class PlayerState(Enum):
    Nothing = 0,
    Opening = 1,
    Buffering = 2,
    Playing = 3,
    Paused = 4,
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

