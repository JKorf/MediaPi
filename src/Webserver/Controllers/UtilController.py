import urllib.parse

from flask import request

from Shared.Events import EventManager
from Shared.Events import EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import ThreadManager
from Shared.Util import to_JSON, current_time, write_size
from Updater import Updater
from Webserver.APIController import app


class UtilController:

    @staticmethod
    @app.route('/util/update', methods=['GET'])
    def get_update():
        return to_JSON(UpdateAvailable(Updater().check_version(), Updater().last_version))

    @staticmethod
    @app.route('/util/update', methods=['POST'])
    def update():
        instance = int(request.args.get("instance"))
        if instance == 1:
            Updater().update()
        else:
            pass  # MasterWebsocketController().send_to_slave(instance, "updater", "update", [])
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
