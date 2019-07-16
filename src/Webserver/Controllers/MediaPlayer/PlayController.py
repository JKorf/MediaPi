import urllib.parse

import sys

from flask import request

from Database.Database import Database
from MediaPlayer.MediaManager import MediaManager
from Shared.Logger import Logger, LogVerbosity
from Webserver.APIController import app, APIController
from Webserver.Controllers.MediaPlayer.TorrentController import TorrentController


class PlayController:

    @staticmethod
    @app.route('/play/movie', methods=['POST'])
    def play_movie():
        instance = int(request.args.get("instance"))
        title = urllib.parse.unquote(request.args.get("title"))
        movie_id = request.args.get("id")
        url = urllib.parse.unquote(request.args.get("url"))
        img = urllib.parse.unquote(request.args.get("img"))
        position = int(request.args.get("position"))

        Logger().write(LogVerbosity.Info, "Play movie " + title + " on " + str(instance))
        if instance == 1:
            MediaManager().start_movie(movie_id, title, url, img, position)
        else:
            APIController().slave_command(instance, "media", "start_movie", movie_id, title, url, img, position)
        return "OK"

    @staticmethod
    @app.route('/play/youtube', methods=['POST'])
    def play_youtube():
        instance = int(request.args.get("instance"))
        title = urllib.parse.unquote(request.args.get("title"))
        url = urllib.parse.unquote(request.args.get("url"))
        position = int(request.args.get("position"))

        Logger().write(LogVerbosity.Info, "Play youtube " + title + " on " + str(instance))
        if instance == 1:
            MediaManager().start_youtube(title, url, position)
        else:
            APIController().slave_command(instance, "media", "start_youtube", title, url, position)
        return "OK"

    @staticmethod
    @app.route('/play/episode', methods=['POST'])
    def play_episode():
        instance = int(request.args.get("instance"))
        title = urllib.parse.unquote(request.args.get("title"))
        movie_id = request.args.get("id")
        url = urllib.parse.unquote(request.args.get("url"))
        img = urllib.parse.unquote(request.args.get("img"))
        position = int(request.args.get("position"))
        season = int(request.args.get("season"))
        episode = int(request.args.get("episode"))

        Logger().write(LogVerbosity.Info, "Play episode " + title + " on " + str(instance))
        if instance == 1:
            MediaManager().start_episode(movie_id, season, episode, title, url, img, position)
        else:
            APIController().slave_command(instance, "media", "start_episode", movie_id, season, episode, title, url, img, position)
        return "OK"

    @staticmethod
    @app.route('/play/torrent', methods=['POST'])
    def play_torrent():
        instance = int(request.args.get("instance"))
        title = urllib.parse.unquote(request.args.get("title"))
        url = urllib.parse.unquote(request.args.get("url"))
        magnet_uri = TorrentController.get_magnet_url(url)
        if magnet_uri is None:
            Logger().write(LogVerbosity.Error, "Failed to find torrent magnet uri")
            return "OK"

        Logger().write(LogVerbosity.Info, "Play torrent " + title + " on " + str(instance))
        if instance == 1:
            MediaManager().start_torrent(title, magnet_uri)
        else:
            APIController().slave_command(instance, "media", "start_torrent", title, magnet_uri)
        return "OK"

    @staticmethod
    @app.route('/play/radio', methods=['POST'])
    def play_radio():
        radio_id = int(request.args.get("id"))
        radio = [x for x in Database().get_radios() if x.id == radio_id][0]
        instance = int(request.args.get("instance"))

        Logger().write(LogVerbosity.Info, "Play radio " + radio.title + " on " + str(instance))
        if instance == 1:
            MediaManager().start_radio(radio.title, radio.url)
        else:
            APIController().slave_command(instance, "media", "start_radio", radio.title, radio.url)
        return "OK"

    @staticmethod
    @app.route('/play/file', methods=['POST'])
    def play_file():
        instance = int(request.args.get("instance"))
        position = int(request.args.get("position"))
        file = urllib.parse.unquote(request.args.get("path"))
        if sys.platform == "win32":
            file = "C:" + file

        Logger().write(LogVerbosity.Info, "Play file " + file + " on " + str(instance))

        if instance == 1:
            MediaManager().start_file(file, position)
        else:
            APIController().slave_command(instance, "media", "start_file", file, position)
        return "OK"

    @staticmethod
    @app.route('/play/url', methods=['POST'])
    def play_url():
        instance = int(request.args.get("instance"))
        title = urllib.parse.unquote(request.args.get("title"))
        url = urllib.parse.unquote(request.args.get("url"))
        Logger().write(LogVerbosity.Info, "Play url " + title + "(" + url + ") on " + str(instance))

        if instance == 1:
            MediaManager().start_url(title, url)
        else:
            APIController().slave_command(instance, "media", "start_url", title, url)
        return "OK"

    @staticmethod
    @app.route('/player/subtitle', methods=['POST'])
    def change_subtitle():
        instance = int(request.args.get("instance"))
        track = int(request.args.get("track"))
        Logger().write(LogVerbosity.Info, "Set subtitle on " + str(instance) + " to " + str(track))

        if instance == 1:
            MediaManager().change_subtitle(track)
        else:
            APIController().slave_command(instance, "media", "change_subtitle", track)
        return "OK"

    @staticmethod
    @app.route('/player/audio', methods=['POST'])
    def change_audio():
        instance = int(request.args.get("instance"))
        track = int(request.args.get("track"))
        Logger().write(LogVerbosity.Info, "Set audio on " + str(instance) + " to " + str(track))

        if instance == 1:
            MediaManager().change_audio(track)
        else:
            APIController().slave_command(instance, "media", "change_audio", track)
        return "OK"

    @staticmethod
    @app.route('/player/stop', methods=['POST'])
    def stop_player():
        instance = int(request.args.get("instance"))
        Logger().write(LogVerbosity.Info, "Stop playing on " + str(instance))

        if instance == 1:
            MediaManager().stop_play()
        else:
            APIController().slave_command(instance, "media", "stop_play")
        return "OK"

    @staticmethod
    @app.route('/player/pause_resume', methods=['POST'])
    def pause_resume_player():
        instance = int(request.args.get("instance"))
        Logger().write(LogVerbosity.Info, "Pause/resume on " + str(instance))

        if instance == 1:
            MediaManager().pause_resume()
        else:
            APIController().slave_command(instance, "media", "pause_resume")
        return "OK"

    @staticmethod
    @app.route('/player/volume', methods=['POST'])
    def change_volume():
        instance = int(request.args.get("instance"))
        volume = int(request.args.get("volume"))
        Logger().write(LogVerbosity.Info, "Set volume on " + str(instance) + " to " + str(volume))

        if instance == 1:
            MediaManager().change_volume(volume)
        else:
            APIController().slave_command(instance, "media", "change_volume", volume)
        return "OK"

    @staticmethod
    @app.route('/player/sub_delay', methods=['POST'])
    def change_sub_delay():
        instance = int(request.args.get("instance"))
        delay = int(request.args.get("delay"))
        Logger().write(LogVerbosity.Info, "Set sub delay on " + str(instance) + " to " + str(delay))

        if instance == 1:
            MediaManager().change_subtitle_delay(delay)
        else:
            APIController().slave_command(instance, "media", "change_subtitle_delay", delay)
        return "OK"

    @staticmethod
    @app.route('/player/seek', methods=['POST'])
    def seek():
        instance = int(request.args.get("instance"))
        position = int(request.args.get("position"))
        Logger().write(LogVerbosity.Info, "Seek " + str(instance) + " to " + str(position))

        if instance == 1:
            MediaManager().seek(position)
        else:
            APIController().slave_command(instance, "media", "seek", position)
        return "OK"
