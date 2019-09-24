from flask import request

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.APIController import app
import urllib.parse


class DataController:

    @staticmethod
    @app.route('/data/favorites', methods=['GET'])
    def get_favorites():
        Logger().write(LogVerbosity.Debug, "Getting favorites")
        return to_JSON(Database().get_favorites())

    @staticmethod
    @app.route('/data/history', methods=['GET'])
    def get_history():
        Logger().write(LogVerbosity.Debug, "Getting history")
        return to_JSON(Database().get_history())

    @staticmethod
    @app.route('/data/history_url', methods=['GET'])
    def get_history_for_url():
        url = request.args.get('url')
        Logger().write(LogVerbosity.Debug, "Getting history")
        return to_JSON(Database().get_history_for_url(urllib.parse.unquote(url)))

    @staticmethod
    @app.route('/data/unfinished', methods=['GET'])
    def get_unfinished_items():
        Logger().write(LogVerbosity.Debug, "Getting unfinished items")
        return to_JSON(Database().get_watching_items())


