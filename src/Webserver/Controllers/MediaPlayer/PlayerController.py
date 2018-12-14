from MediaPlayer.MediaPlayer import MediaManager
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Webserver.Controllers.Websocket.MasterWebsocketController import MasterWebsocketController


class PlayerController:

    @staticmethod
    def set_subtitle_file(file):
        Logger.write(2, "Setting subtitle file: " + file)
        EventManager.throw_event(EventType.SetSubtitleFiles, [[file]])

    @staticmethod
    def set_subtitle_id(sub):
        Logger.write(2, "Setting subtitle id")
        EventManager.throw_event(EventType.SetSubtitleId, [int(sub)])

    @staticmethod
    def stop_player(instance):
        Logger.write(2, "Stop player")

        if Settings.get_string("name") == instance:
            MediaManager().stop_play()
        else:
            MasterWebsocketController().send_to_slave(instance, "play_stop", [])

    @staticmethod
    def pause_resume_player():
        Logger.write(2, "Pause/resume player")
        EventManager.throw_event(EventType.PauseResumePlayer, [])

    @staticmethod
    def change_volume(vol):
        Logger.write(2, "Change volume")
        EventManager.throw_event(EventType.SetVolume, [int(vol)])

    @staticmethod
    def change_subtitle_offset(offset):
        Logger.write(2, "Change subtitle offset: " + offset)
        EventManager.throw_event(EventType.SetSubtitleOffset, [int(float(offset) * 1000 * 1000)])

    @staticmethod
    def seek(pos):
        Logger.write(2, "Seek " + pos)
        EventManager.throw_event(EventType.Seek, [int(float(pos)) * 1000])

    @staticmethod
    def set_audio_track(track):
        Logger.write(2, "Set audio track " + track)
        EventManager.throw_event(EventType.SetAudioId, [int(track)])
