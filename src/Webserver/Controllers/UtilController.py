import urllib.parse

from flask import request

from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON, write_size
from Updater import Updater
from Webserver.APIController import app, APIController


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


class UpdateAvailable:

    def __init__(self, available, commit_hash):
        self.available = available
        self.hash = commit_hash
