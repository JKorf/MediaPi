import json
import os
import urllib.parse

from Managers.TorrentManager import TorrentManager
from MediaPlayer.Util.Util import try_parse_season_episode, is_media_file
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import RequestFactory, Singleton
from UI.TV.VLCPlayer import VLCPlayer, PlayerState
from UI.Web.Server.Models import FileStructure


class NextEpisodeManager(metaclass=Singleton):

    def __init__(self,):
        EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)
        EventManager.register_event(EventType.PlayerStopped, self.player_stopped)

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

    def player_stopped(self, position, length):
        if not length:
            return

        factor = float(position) / float(length)
        if length - position < 60 and length != position and factor > 0.9:
            self.notify_next_episode()

    def player_state_change(self, old_state, new_state):
        if new_state == PlayerState.Playing:
            self.check_next_episode()
        elif new_state == PlayerState.Nothing:
            self.reset()
        elif new_state == PlayerState.Ended:
            self.notify_next_episode()

    def notify_next_episode(self):
        if self.next_type is not None:
            Logger.write(2, "Continuing next episode: " + self.next_title)
            EventManager.throw_event(EventType.NextEpisodeSelection, [self.next_path,
                                                                      self.next_title,
                                                                      self.next_season,
                                                                      self.next_episode,
                                                                      self.next_type,
                                                                      self.next_media_file,
                                                                      self.next_img])

    def check_next_episode(self):
        if VLCPlayer().type == "Radio" or VLCPlayer().type == "YouTube" or VLCPlayer().type == "Image":
            self.reset()
            return

        if VLCPlayer().type == "File":
            self.reset()
            # Try to get next episode from same folder
            season, epi = try_parse_season_episode(VLCPlayer().path)
            if season == 0 or epi == 0:
                Logger.write(2, "No next episode of file, season/epi not parsed")
                return

            if Settings.get_bool("slave"):
                index = VLCPlayer().path.index("/file/")
                dir_name = os.path.dirname(VLCPlayer().path[index + 6:])

                data = RequestFactory.make_request(Settings.get_string("master_ip") + "/hd/directory?path=" + dir_name, "GET")
                result = json.loads(data.decode("utf8"))
                file_list = result["files"]
            else:
                dir_name = os.path.dirname(VLCPlayer().path)
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
                    return
            Logger.write(2, "No next episode of file, no matching next season/epi found in file list")
            return

        season, epi = try_parse_season_episode(TorrentManager().torrent.media_file.path)
        if season == 0 or epi == 0:
            Logger.write(2, "No next episode found, season/epi not parsed")
            return

        # Try to get next episode from same torrent
        for file in TorrentManager().torrent.files:
            if not is_media_file(file.path):
                continue

            s, e = try_parse_season_episode(file.path)
            if s == season and e == epi + 1:
                Logger.write(2, "Found next episode: " + file.path)
                self.next_season = s
                self.next_episode = epi + 1
                self.next_type = "Torrent"
                self.next_title = VLCPlayer().title.replace("E" + self.add_leading_zero(epi), "E" + self.add_leading_zero(epi + 1))
                self.next_path = TorrentManager().torrent.uri
                self.next_media_file = file.name
                return

        #  Try to get next episode from shows list
        season, epi = try_parse_season_episode(VLCPlayer().title)
        if season == 0 or epi == 0:
            Logger.write(2, "No next episode of show, season/epi not parsed")
            return

        show = VLCPlayer().title[8:]
        results = json.loads(RequestFactory.make_request("http://127.0.0.1/shows/get_shows?page=1&orderby=trending&keywords=" + urllib.parse.quote(show)).decode('utf8'))
        if len(results) == 0:
            Logger.write(2, "No next episode of show, request returned no results for shows")
            return

        show = json.loads(RequestFactory.make_request("http://127.0.0.1/shows/get_show?id=" + urllib.parse.quote(results[0]["_id"])).decode('utf8'))
        next_epi = [x for x in show["episodes"] if x["season"] == season and x["episode"] == epi + 1]
        if len(next_epi) == 0:
            Logger.write(2, "No next episode of show, request returned no results for next epi")
            return

        Logger.write(2, "Found next episode: " + next_epi[0]["title"])
        self.next_season = season
        self.next_episode = epi + 1
        self.next_type = "Torrent"
        self.next_title = VLCPlayer().title.replace("E" + self.add_leading_zero(epi), "E" + self.add_leading_zero(epi + 1))
        self.next_path = next_epi[0]["torrents"]["0"]["url"]
        self.next_img = VLCPlayer().img

    def add_leading_zero(self, val):
        i = int(val)
        if i < 10:
            return "0" + str(i)
        return str(i)
