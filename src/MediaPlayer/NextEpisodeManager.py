import json
import os

import asyncio

from MediaPlayer.Util.Util import try_parse_season_episode, is_media_file
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import Singleton
from Webserver.Controllers.MediaPlayer.ShowController import ShowController
from Webserver.Models import FileStructure


class NextEpisodeManager(metaclass=Singleton):

    def __init__(self,):
        self.next_id = None
        self.next_type = None
        self.next_path = None
        self.next_title = None
        self.next_media_file = None
        self.next_img = None
        self.next_season = 0
        self.next_episode = 0

    def reset(self):
        Logger().write(2, "Resetting next episode manager")
        self.next_id = None
        self.next_img = None
        self.next_type = None
        self.next_path = None
        self.next_title = None
        self.next_media_file = None
        self.next_season = 0
        self.next_episode = 0

    def notify_next_episode(self, callback, callback_no_answer):
        if self.next_type is not None:
            Logger().write(2, "Can continue with next episode: " + self.next_title)
            EventManager.throw_event(EventType.ClientRequest, [callback, callback_no_answer, 1000 * 60 * 1, "SelectNextEpisode", [self.next_title]])

    def check_next_episode(self, media_data, torrent):
        if media_data.type == "Radio" or media_data.type == "YouTube":
            return

        if media_data.type == "File":
            self.try_find_in_dir(media_data)
        elif media_data.type == "Show":
            self.try_find_in_shows(media_data)
        elif media_data.type == "Torrent":
            self.try_find_in_torrent(media_data, torrent)

    def try_find_in_shows(self, media_data):
        #  Try to get next episode from shows list
        season, epi = try_parse_season_episode(media_data.title)
        if season == 0 or epi == 0:
            Logger().write(2, "No next episode of show, season/epi not parsed")
            return

        loop = asyncio.get_event_loop()
        raw_data = loop.run_until_complete(ShowController.get_by_id(media_data.id))

        if raw_data is None:
            Logger().write(2, "No next episode of show, request failed")
            return


        show = json.loads(raw_data.decode("utf-8"))
        next_epi = [x for x in show["episodes"] if x["season"] == season and x["episode"] == epi + 1]
        if len(next_epi) == 0:
            Logger().write(2, "No next episode of show, request returned no results for next epi")
            return

        Logger().write(2, "Found next episode: " + next_epi[0]["title"])
        self.next_id = media_data.id
        self.next_season = season
        self.next_episode = epi + 1
        self.next_type = "Show"
        self.next_title = media_data.title.replace("E" + self.add_leading_zero(epi), "E" + self.add_leading_zero(epi + 1))
        self.next_path = next_epi[0]["torrents"]["0"]["url"]
        self.next_img = media_data.image

    def try_find_in_torrent(self, media_data, torrent):
        season, epi = try_parse_season_episode(torrent.media_file.path)
        if season == 0 or epi == 0:
            Logger().write(2, "No next episode found, season/epi not parsed")
            return

        # Try to get next episode from same torrent
        for file in torrent.files:
            if not is_media_file(file.path):
                continue

            s, e = try_parse_season_episode(file.path)
            if s == season and e == epi + 1:
                Logger().write(2, "Found next episode: " + file.path)
                self.next_season = s
                self.next_episode = epi + 1
                self.next_type = "Torrent"
                self.next_title = torrent.media_file.name.replace("E" + self.add_leading_zero(epi), "E" + self.add_leading_zero(epi + 1))
                self.next_path = torrent.uri
                self.next_media_file = file.name
                return

    def try_find_in_dir(self, media_data):
        season, epi = try_parse_season_episode(media_data.url)
        if season == 0 or epi == 0:
            Logger().write(2, "No next episode of file, season/epi not parsed")
            return

        dir_name = os.path.dirname(media_data.url)
        if Settings.get_bool("slave"):
            data = RequestFactory.make_request(Settings.get_string("master_ip") + "/hd/directory?path=" + dir_name, "GET")
            result = json.loads(data.decode("utf8"))
            file_list = result["files"]
        else:
            file_list = FileStructure(dir_name).file_names

        for potential in file_list:
            if not is_media_file(potential):
                continue

            s, e = try_parse_season_episode(potential)
            if s == season and e == epi + 1:
                Logger().write(2, "Found next episode: " + potential)
                self.next_season = s
                self.next_episode = epi + 1
                self.next_type = "File"
                self.next_title = potential
                self.next_path = dir_name + "/" + potential
                return
        Logger().write(2, "No next episode of file, no matching next season/epi found in file list")
        return

    @staticmethod
    def add_leading_zero(val):
        i = int(val)
        if i < 10:
            return "0" + str(i)
        return str(i)
