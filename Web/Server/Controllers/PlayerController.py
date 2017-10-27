from Shared.Events import EventManager, EventType
from Shared.Logger import Logger


class PlayerController:

    @staticmethod
    def set_subtitle_file(file):
        Logger.write(2, "Setting subtitle file: " + file)
        # file = file.replace('/', '\\')
        EventManager.throw_event(EventType.SetSubtitleFile, [file])

    @staticmethod
    def set_subtitle_id(sub):
        Logger.write(2, "Setting subtitle id")
        EventManager.throw_event(EventType.SetSubtitleId, [int(sub)])

    @staticmethod
    def stop_player():
        Logger.write(2, "Stop player")
        EventManager.throw_event(EventType.StopPlayer, [])
        EventManager.throw_event(EventType.StopStreamTorrent, [])

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
        EventManager.throw_event(EventType.InitialSeeking, [int(float(pos)) * 1000])

    @staticmethod
    def set_audio_track(track):
        Logger.write(2, "Set audio track " + track)
        EventManager.throw_event(EventType.SetAudioId, [int(track)])
