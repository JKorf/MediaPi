import urllib.parse

import sys

from Database.Database import Database
from MediaPlayer.MediaManager import MediaManager
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.BaseHandler import BaseHandler
from Webserver.Controllers.MediaPlayer.RadioController import RadioController
from Webserver.Controllers.MediaPlayer.TorrentProvider import Torrent
from Webserver.Controllers.Websocket.MasterWebsocketController import MasterWebsocketController


class PlayController(BaseHandler):
    async def get(self, url):
        if url == "history":
            self.write(to_JSON(Database().get_history()))

    async def post(self, url):
        instance = int(self.get_argument("instance"))
        # ------------ Play movie --------------
        if url == "movie":
            title = self.get_argument("title")
            Logger().write(LogVerbosity.Info, "Play movie " + title + " on " + str(instance))
            if MasterWebsocketController().is_self(instance):
                MediaManager().start_movie(self.get_argument("id"), urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), urllib.parse.unquote(self.get_argument("img")), int(self.get_argument("position")))
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "start_movie", [self.get_argument("id"), urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), urllib.parse.unquote(self.get_argument("img")), int(self.get_argument("position"))])

        # ------------ Play episode --------------
        elif url == "episode":
            title = self.get_argument("title")
            Logger().write(LogVerbosity.Info, "Play episode " + title + " on " + str(instance))
            if MasterWebsocketController().is_self(instance):
                MediaManager().start_episode(self.get_argument("id"), self.get_argument("season"), self.get_argument("episode"), urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), urllib.parse.unquote(self.get_argument("img")), int(self.get_argument("position")))
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "start_episode", [self.get_argument("id"), self.get_argument("season"), self.get_argument("episode"), urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), urllib.parse.unquote(self.get_argument("img")), int(self.get_argument("position"))])

        # ------------ Play torrent --------------
        elif url == "torrent":
            title = self.get_argument("title")
            Logger().write(LogVerbosity.Info, "Play torrent " + title + " on " + str(instance))
            if MasterWebsocketController().is_self(instance):
                MediaManager().start_torrent(urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(Torrent.get_magnet_uri(self.get_argument("url"))))
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "start_torrent",
                                                          [urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(Torrent.get_magnet_uri(self.get_argument("url")))])

        # ------------ Play radio --------------
        elif url == "radio":
            radio = RadioController.get_by_id(int(self.get_argument("id")))
            Logger().write(LogVerbosity.Info, "Play radio " + radio.title + " on " + str(instance))
            if MasterWebsocketController().is_self(instance):
                MediaManager().start_radio(radio.title, radio.url)
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "start_radio", [radio.id])

        # ------------ Play file --------------
        elif url == "file":
            file = urllib.parse.unquote(self.get_argument("path"))
            if sys.platform == "win32":
                file = "C:" + file

            Logger().write(LogVerbosity.Info, "Play file " + file + " on " + str(instance))

            if MasterWebsocketController().is_self(instance):
                MediaManager().start_file(file, int(self.get_argument("position")))
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "start_file", [file, int(self.get_argument("position"))])

        # ------------ Play url --------------
        elif url == "url":
            title = urllib.parse.unquote(self.get_argument("title"))
            url = urllib.parse.unquote(self.get_argument("url"))
            Logger().write(LogVerbosity.Info, "Play url " + title + "(" + url + ") on " + str(instance))

            if MasterWebsocketController().is_self(instance):
                MediaManager().start_url(title, url)
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "start_url", [title, url])

        elif url == "change_subtitle":
            track = int(self.get_argument("track"))
            Logger().write(LogVerbosity.Info, "Set subtitle on " + str(instance) + " to " + str(track))

            if MasterWebsocketController().is_self(instance):
                MediaManager().change_subtitle(track)
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "change_subtitle", [track])

        elif url == "change_audio":
            track = int(self.get_argument("track"))
            Logger().write(LogVerbosity.Info, "Set audio on " + str(instance) + " to " + str(track))

            if MasterWebsocketController().is_self(instance):
                MediaManager().change_audio(track)
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "change_audio", [track])

        elif url == "stop_player":
            Logger().write(LogVerbosity.Info, "Stop playing on " + str(instance))

            if MasterWebsocketController().is_self(instance):
                MediaManager().stop_play()
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "stop_play", [])
        elif url == "pause_resume_player":
            Logger().write(LogVerbosity.Info, "Pause/resume playing on " + str(instance))

            if MasterWebsocketController().is_self(instance):
                MediaManager().pause_resume()
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "pause_resume", [])
        elif url == "change_volume":
            volume = int(self.get_argument("volume"))
            Logger().write(LogVerbosity.Info, "Set volume on " + str(instance) + " to " + str(volume))

            if MasterWebsocketController().is_self(instance):
                MediaManager().change_volume(volume)
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "change_volume", [volume])
        elif url == "change_sub_delay":
            delay = int(self.get_argument("delay"))
            Logger().write(LogVerbosity.Info, "Set sub delay on " + str(instance) + " to " + str(delay))

            if MasterWebsocketController().is_self(instance):
                MediaManager().change_subtitle_delay(delay)
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "change_subtitle_delay", [delay])
        elif url == "seek":
            position = int(self.get_argument("position"))
            Logger().write(LogVerbosity.Info, "Seek " + str(instance) + " to " + str(position))

            if MasterWebsocketController().is_self(instance):
                MediaManager().seek(position)
            else:
                MasterWebsocketController().send_to_slave(instance, "media", "seek", [position])