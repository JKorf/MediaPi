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
        Logger().write(LogVerbosity.Important, "============== Test ===============")
        EventManager.throw_event(EventType.Log, [])
        Logger().write(LogVerbosity.Important, "-- Threads --")
        for thread_list in sorted(ThreadManager().thread_history.values(), key=lambda x: len(x), reverse=True):
            Logger().write(LogVerbosity.Important, "     " + thread_list[0].thread_name + " " + str(len(thread_list)) + " entries, averages " + str(sum(c.end_time - c.start_time for c in thread_list if c.end_time != 0) / len(thread_list)) + "ms")
            for thread in [x for x in thread_list if x.end_time == 0]:
                Logger().write(LogVerbosity.Important, "         Currently running for " + str((current_time() - thread.start_time)/1000) + " seconds")
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
