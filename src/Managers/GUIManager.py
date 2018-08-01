import sys

from Interface.TV.GUI import GUI
from Interface.TV.VLCPlayer import VLCPlayer, PlayerState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Threading import CustomThread


class GUIManager:

    def __init__(self, program):
        self.program = program
        self.gui = None
        self.app = None
        self.player = VLCPlayer()
        self.youtube_end_counter = 0

        self.player.on_state_change(self.player_state_change)

        EventManager.register_event(EventType.StartPlayer, self.start_player)
        EventManager.register_event(EventType.StopPlayer, self.stop_player)
        EventManager.register_event(EventType.PauseResumePlayer, self.pause_resume_player)
        EventManager.register_event(EventType.SetVolume, self.set_volume)
        EventManager.register_event(EventType.Seek, self.seek)

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

    def start_player(self, type, title, url, img=None, position=0):
        self.stop_player()
        self.player.play(type, title, url, img, position)

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