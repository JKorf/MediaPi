from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.BaseHandler import BaseHandler
import urllib.parse


class DataController(BaseHandler):
    async def get(self, url):
        if url == "get_favorites":
            Logger().write(LogVerbosity.Debug, "Getting favorites")
            self.write(to_JSON(Database().get_favorites()))

        if url == "get_history":
            Logger().write(LogVerbosity.Debug, "Getting history")
            self.write(to_JSON(Database().get_history()))

        if url == "get_history_for_url":
            Logger().write(LogVerbosity.Debug, "Getting history")
            self.write(to_JSON(Database().get_history_for_url(urllib.parse.unquote(self.get_argument("url")))))

        if url == "get_unfinished_items":
            Logger().write(LogVerbosity.Debug, "Getting unfinished items")
            self.write(to_JSON(Database().get_watching_items()))
