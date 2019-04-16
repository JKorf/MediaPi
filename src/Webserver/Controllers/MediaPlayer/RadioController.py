from flask import request

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.Models import BaseMedia
from Webserver.APIController import app


class Radio(BaseMedia):

    def __init__(self, radio_id, title, url, poster):
        super().__init__(radio_id, poster, title)
        self.url = url


class RadioController:

    @staticmethod
    @app.route('/radios', methods=['GET'])
    def get():
        Logger().write(LogVerbosity.Debug, "Get radio list")
        return to_JSON(Database().get_radios())