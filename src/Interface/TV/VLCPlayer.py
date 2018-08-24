import datetime
import os
import time
from enum import Enum

from Interface.TV import vlc
from Interface.TV.vlc import libvlc_get_version, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import current_time


class VLCPlayer:

    def __init__(self):
        self.__end_action = None
        self.__vlc_instance = None

        self.instantiate_vlc()

        self.__player = self.__vlc_instance.media_player_new()
        self.__event_manager = self.__player.event_manager()
        self.hook_events()

        self.set_volume(75)

        self.type = None
        self.title = None
        self.path = None
        self.img = None
        self.time = 0
        self.filename = None
        self.prepared = False

        self.state = PlayerState.Nothing
        self.state_change_action = None
        self.trying_subitems = False

        thread = CustomThread(self.watch_time_change, "VLC State watcher")
        thread.start()

    def instantiate_vlc(self):
        parameters = self.get_instance_parameters()
        Logger.write(2, "VLC parameters: " + str(parameters))
        self.__vlc_instance = vlc.Instance("vlc", *parameters)
        Logger.write(3, "VLC version " + libvlc_get_version().decode('utf8'))

    def prepare_play(self, type, title, url, img=None, time=0, filename=None):
        self.type = type
        self.title = title
        self.path = url
        self.img = img
        self.time = time
        self.filename = filename
        self.prepared = True

    def play(self, time=0, filename=None):
        if not self.prepared:
            raise ValueError("Player not prepared")

        if time != 0:
            self.time = time
        if filename is not None:
            self.filename = filename

        parameters = self.get_play_parameters()

        Logger.write(2, "VLC Play | Type: " + self.type)
        Logger.write(2, "VLC Play | Title: " + self.title)
        Logger.write(2, "VLC Play | Url: " + self.path)
        Logger.write(2, "VLC Play | Time: " + str(self.time))
        Logger.write(2, "VLC Play | Filename: " + str(self.filename))
        Logger.write(2, "VLC Play | Parameters: " + str(parameters))

        self.__player.set_mrl(self.path, *parameters)
        return self.__player.play() != -1

    def get_instance_parameters(self):
        params = []
        params.append("--verbose=" + str(Settings.get_int("vlc_log_level")))
        params.append("--network-caching=" + str(Settings.get_int("network_caching")))
        params.append("--ipv4-timeout=500")
        params.append("--image-duration=-1")

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
        if self.type == "YouTube":
            params.append("lua-intf=youtube")

        if self.time != 0:
            params.append("start-time=" + str(self.time // 1000))

        if self.type != "File":
            if self.time != 0 and self.filename.endswith("mp4"):
                params.append("demux=avformat")
            elif self.filename is not None and self.filename.endswith("avi"):
                params.append("demux=avformat")
        return params

    def pause_resume(self):
        self.__player.pause()

    def stop(self):
        self.__player.stop()
        self.type = None
        self.title = None
        self.img = None
        self.path = None
        self.prepared = False

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

    def set_subtitle_file(self, file):
        file = file.replace("/", os.sep).replace("\\", os.sep)
        # NOTE this must be called after Play()
        return self.__player.video_set_subtitle_file(file)

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

    def on_state_change(self, action):
        self.state_change_action = action

    def hook_events(self):
        self.__event_manager.event_attach(EventType.MediaPlayerOpening, self.state_change_opening)
        self.__event_manager.event_attach(EventType.MediaPlayerPlaying, self.state_change_playing)
        self.__event_manager.event_attach(EventType.MediaPlayerPaused, self.state_change_paused)
        self.__event_manager.event_attach(EventType.MediaPlayerStopped, self.state_change_stopped)
        self.__event_manager.event_attach(EventType.MediaPlayerEndReached, self.state_change_end_reached)
        self.__event_manager.event_attach(EventType.MediaPlayerEncounteredError, self.on_error)

    def state_change_opening(self, event):
        if self.state != PlayerState.Opening:
            self.change_state(PlayerState.Opening)

    def state_change_playing(self, event):
        if self.state == PlayerState.Paused:
            self.change_state(PlayerState.Playing)
        else:
            pass # gets handled by watching time change

    def state_change_paused(self, event):
        if self.state != PlayerState.Paused:
            self.change_state(PlayerState.Paused)

    def state_change_stopped(self, event):
        if self.state != PlayerState.Nothing:
            self.prepared = False
            self.change_state(PlayerState.Nothing)

    def state_change_end_reached(self, event):
        if self.state != PlayerState.Ended:
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
                if self.state == PlayerState.Playing:
                    self.change_state(PlayerState.Buffering)
            else:
                if self.state == PlayerState.Buffering or self.state == PlayerState.Opening:
                    self.change_state(PlayerState.Playing)
            last_time = this_time
            time.sleep(1)

    def change_state(self, new):
        old = self.state
        self.state = new
        self.state_change_action(old, self.state)


class MediaItem:

    def __init__(self, type, title, url, img):
        self.type = type
        self.title = title
        self.url = url
        self.img = img


class PlayerState(Enum):
    Nothing = 0,
    Opening = 1,
    Buffering = 2,
    Playing = 3,
    Paused = 4,
    Ended = 5

