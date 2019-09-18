import os
import time
import urllib.parse

import sys

import objgraph
from flask import request

from Database.Database import Database
from MediaPlayer.MediaManager import MediaManager
from MediaPlayer.Player.VLCPlayer import VLCPlayer
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory
from Shared.Util import to_JSON, write_size, current_time
from Updater import Updater
from Webserver.APIController import app, APIController
from Webserver.Controllers.MediaPlayer.MovieController import MovieController
from Webserver.Controllers.MediaPlayer.ShowController import ShowController
from Webserver.Controllers.MediaPlayer.TorrentController import TorrentController


class UtilController:

    health_cache = dict()

    @staticmethod
    @app.route('/util/update', methods=['GET'])
    def get_update():
        instance = int(request.args.get("instance"))
        if instance == 1:
            return to_JSON(UpdateAvailable(Updater().check_version(), Updater().last_version))
        else:
            result = APIController().slave_request(instance, "get_last_version", 10)
            if result is None:
                return to_JSON(UpdateAvailable(False, ""))
            return to_JSON(UpdateAvailable(result[0], result[1]))

    @staticmethod
    @app.route('/util/get_action_history', methods=['GET'])
    def get_action_history():
        device_id = request.args.get("device_id")
        topic = request.args.get("topic")
        start_time = int(request.args.get("start"))
        end_time = int(request.args.get("end"))

        return to_JSON(Database().get_action_history(device_id, topic, start_time, end_time))

    @staticmethod
    @app.route('/util/update', methods=['POST'])
    def update():
        instance = int(request.args.get("instance"))
        if instance == 1:
            Updater().update()
        else:
            APIController().slave_command(instance, "updater", "update")
        return "OK"

    @staticmethod
    @app.route('/util/restart_device', methods=['POST'])
    def restart_device():
        instance = int(request.args.get("instance"))
        if instance == 1:
            os.system('sudo reboot')
        else:
            APIController().slave_command(instance, "system", "restart_device")
        return "OK"

    @staticmethod
    @app.route('/util/restart_application', methods=['POST'])
    def restart_application():
        instance = int(request.args.get("instance"))
        if instance == 1:
            python = sys.executable
            os.execl(python, python, *sys.argv)
        else:
            APIController().slave_command(instance, "system", "restart_application")
        return "OK"

    @staticmethod
    @app.route('/util/close_application', methods=['POST'])
    def close_application():
        instance = int(request.args.get("instance"))
        if instance == 1:
            sys.exit()
        else:
            APIController().slave_command(instance, "system", "close_application")
        return "OK"

    @staticmethod
    @app.route('/util/log', methods=['POST'])
    def debug_log():
        Logger().write(LogVerbosity.Important, "Test")
        return "OK"

    @staticmethod
    @app.route('/util/logs', methods=['GET'])
    def get_log_files():
        log_files = Logger.get_log_files()
        return to_JSON([(name, path, write_size(size)) for name, path, size in log_files])

    @staticmethod
    @app.route('/util/log', methods=['GET'])
    def get_log_file():
        file = urllib.parse.unquote(request.args.get('file'))
        return Logger.get_log_file(file)

    @staticmethod
    @app.route('/util/shelly', methods=['POST'])
    def shelly():
        ip = request.args.get("ip")
        state = "on" if request.args.get("state") == "true" else "off"

        Logger().write(LogVerbosity.Info, "Set shelly " + ip + " to " + state)
        result = RequestFactory.make_request("http://" + ip + "?state=" + state)
        if result is not None:
            Logger().write(LogVerbosity.Info, result)
        return "OK"

    @staticmethod
    @app.route('/util/system_health_check', methods=['POST'])
    def execute_health_test():
        Logger().write(LogVerbosity.Info, "System health test")
        result = HealthTestResult()

        UtilController.run_endpoint_checks(result)
        UtilController.run_torrent_check(result)

        return to_JSON(result)

    @staticmethod
    def run_endpoint_checks(result):
        movies = MovieController.request_movies(MovieController.movies_api_path + "movies/1?sort=Trending")
        shows = ShowController.request_shows(ShowController.shows_api_path + "shows/1?sort=Trending")
        torrents = TorrentController.get_torrents(TorrentController.base_url + "/top-100-movies")

        result.request_movies_result.set_result(len(movies) != 0, "No movies returned")
        result.request_shows_result.set_result(len(shows) != 0, "No shows returned")
        result.request_torrents_result.set_result(len(torrents) != 0, "No torrents returned")

        return result

    @staticmethod
    def run_torrent_check(result):
        best_movie_torrents = MovieController.request_movies(MovieController.movies_api_path + "movies/1?sort=Trending")[0: 20]
        all_torrents = []
        for arr in [x.torrents for x in best_movie_torrents]:
            all_torrents += arr

        if len(all_torrents) == 0:
            return

        torrent = max(all_torrents, key=lambda t: t.seeds / (t.peers or 1))
        Logger().write(LogVerbosity.Info,
                       "System health selected torrent at " + torrent.quality + ", " + str(torrent.peers) + "/" + str(torrent.seeds) + " l/s")

        MediaManager().start_movie(0, "Health check", torrent.url, None, 0)

        created = UtilController.wait_for(2000, lambda: MediaManager().torrent is not None)
        result.torrent_starting_result.set_result(created, "Didn't create torrent")
        if not created:
            return result

        executing = UtilController.wait_for(10000, lambda: MediaManager().torrent.is_preparing or MediaManager().torrent.is_executing)
        result.torrent_starting_result.set_result(executing, "Torrent isn't executing")
        if not executing:
            return result

        downloading = UtilController.wait_for(10000, lambda: MediaManager().torrent.network_manager.average_download_counter.total > 0)
        result.torrent_downloading_result.set_result(downloading, "No bytes downloaded at all")

        playing = False
        if downloading:
            playing = UtilController.wait_for(30000, lambda: VLCPlayer().player_state.playing_for > 0)
            result.torrent_playing_result.set_result(playing, "Didn't start playing torrent")

        if playing:
            MediaManager().seek(1000 * 60 * 5) # seek to 5 minutes in
            playing = UtilController.wait_for(10000, lambda: VLCPlayer().player_state.playing_for > 1000 * 60 * 5)
            result.torrent_playing_after_seek_result.set_result(playing, "Didn't start playing torrent after seeking")

        MediaManager().stop_play()

        stopped_event = UtilController.wait_for_event(20000, EventType.TorrentStopped)
        result.torrent_disposing_result.set_result(stopped_event, "Torrent stopped event not received")
        if stopped_event:
            disposed = UtilController.wait_for(5000, lambda: len(objgraph.by_type('MediaPlayer.Torrents.Torrent.Torrent.Torrent')) == 0)
            result.torrent_disposing_result.set_result(disposed, "Torrent not disposed after stopping")

        return result

    @staticmethod
    def wait_for(max_time, action):
        start = current_time()
        while current_time() - start < max_time:
            if action():
                return True
            time.sleep(0.5)
        return False

    @staticmethod
    def wait_for_event(max_time, event):
        UtilController.health_cache[event] = False
        evnt = EventManager.register_event(event, lambda *x: UtilController.assign(event))
        result = UtilController.wait_for(max_time, lambda: UtilController.health_cache[event])
        EventManager.deregister_event(evnt)
        return result

    @staticmethod
    def assign(name):
        UtilController.health_cache[name] = True


class UpdateAvailable:

    def __init__(self, available, commit_hash):
        self.available = available
        self.hash = commit_hash


class HealthTestResult:

    def __init__(self):
        self.request_movies_result = HealthTestResultItem("Fetch movies")
        self.request_shows_result = HealthTestResultItem("Fetch shows")
        self.request_torrents_result = HealthTestResultItem("Fetch torrents")

        self.torrent_starting_result = HealthTestResultItem("Starting torrent")
        self.torrent_downloading_result = HealthTestResultItem("Downloading torrent")
        self.torrent_playing_result = HealthTestResultItem("Playing torrent")
        self.torrent_playing_after_seek_result = HealthTestResultItem("Playing after seek")
        self.torrent_disposing_result = HealthTestResultItem("Disposing torrent")


class HealthTestResultItem:

    def __init__(self, name):
        self.name = name
        self.result = True
        self.run = False
        self.reason = None

    def set_result(self, result, reason):
        self.result = result
        self.run = True
        self.reason = reason
