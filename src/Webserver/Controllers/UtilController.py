import os
import time
import urllib.parse

import sys

import objgraph
from flask import request

from MediaPlayer.MediaManager import MediaManager
from MediaPlayer.Player.VLCPlayer import VLCPlayer
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON, write_size, current_time
from Updater import Updater
from Webserver.APIController import app, APIController
from Webserver.Controllers.MediaPlayer.MovieController import MovieController
from Webserver.Controllers.MediaPlayer.ShowController import ShowController
from Webserver.Controllers.MediaPlayer.TorrentController import TorrentController


class UtilController:

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

        if len(movies) == 0: result.request_movies_result.fail("No movies returned")
        elif len(shows) == 0: result.request_shows_result.fail("No shows returned")
        elif len(torrents) == 0: result.request_torrents_result.fail("No torrents returned")

        return result

    @staticmethod
    def run_torrent_check(result):
        best_movie_torrents = MovieController.request_movies(MovieController.movies_api_path + "movies/1?sort=Trending")[0: 20]
        all_torrents = []
        for arr in [x.torrents for x in best_movie_torrents]:
            all_torrents += arr
        torrent = max(all_torrents, key=lambda t: t.seeds / t.peers)
        Logger().write(LogVerbosity.Info,
                       "System health selected torrent at " + torrent.quality + ", " + str(torrent.peers) +"/" + str(torrent.seeds) + " l/s")

        MediaManager().start_movie(0, "Health check", torrent.url, None, 0)

        created = UtilController.wait_for(2000, lambda: MediaManager().torrent is not None)
        if not created: result.torrent_creating_result.fail("Didn't create torrent")

        executing = UtilController.wait_for(10000, lambda: MediaManager().torrent.is_preparing or MediaManager().torrent.is_executing)
        if not executing: result.torrent_starting_result.fail("Torrent isn't executing")

        downloading = UtilController.wait_for(10000, lambda: MediaManager().torrent.network_manager.average_download_counter.total > 0)
        if not downloading: result.torrent_downloading_result.fail("No bytes downloaded at all")

        playing = UtilController.wait_for(30000, lambda: VLCPlayer().player_state.playing_for > 0)
        if not playing: result.torrent_playing_result.fail("Didn't start playing torrent")

        MediaManager().stop_play()

        disposed = UtilController.wait_for(20000, lambda: len(objgraph.by_type('MediaPlayer.Torrents.Torrent.Torrent.Torrent')) == 0)
        if not disposed: result.torrent_disposing_result.fail("Torrent not disposed after stopping")

        return result

    @staticmethod
    def wait_for(max_time, action):
        start = current_time()
        while current_time() - start < max_time:
            if action():
                return True
            time.sleep(0.5)
        return False


class UpdateAvailable:

    def __init__(self, available, commit_hash):
        self.available = available
        self.hash = commit_hash


class HealthTestResult:

    def __init__(self):
        self.request_movies_result = HealthTestResultItem("Fetch movies")
        self.request_shows_result = HealthTestResultItem("Fetch shows")
        self.request_torrents_result = HealthTestResultItem("Fetch torrents")
        self.torrent_creating_result = HealthTestResultItem("Creating torrent")
        self.torrent_starting_result = HealthTestResultItem("Starting torrent")
        self.torrent_downloading_result = HealthTestResultItem("Downloading torrent")
        self.torrent_playing_result = HealthTestResultItem("Playing torrent")
        self.torrent_disposing_result = HealthTestResultItem("Disposing torrent")


class HealthTestResultItem:

    def __init__(self, name):
        self.name = name
        self.result = True
        self.reason = None

    def fail(self, reason):
        self.result = False
        self.reason = reason
