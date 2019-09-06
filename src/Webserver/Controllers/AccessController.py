from flask import request
import urllib.parse

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.APIController import app


class AccessController:

    @staticmethod
    @app.route('/access/clients', methods=['GET'])
    def get_clients():
        Logger().write(LogVerbosity.Debug, "Getting clients")
        return to_JSON(Database().get_clients())

    @staticmethod
    @app.route('/access/client', methods=['GET'])
    def get_client():
        Logger().write(LogVerbosity.Debug, "Getting client")
        return to_JSON(Database().get_client_access(request.args.get('id')))

    @staticmethod
    @app.route('/access/revoke_client', methods=['POST'])
    def revoke_client():
        Logger().write(LogVerbosity.Debug, "Revoking client")
        Database().remove_client(urllib.parse.unquote(request.args.get('key')))
        return "OK"
