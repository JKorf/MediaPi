import os
import urllib.parse

from Shared.Events import EventManager
from Shared.Events import EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import ThreadManager
from Shared.Util import to_JSON, current_time, write_size
from Updater import Updater
from Webserver.BaseHandler import BaseHandler
from Webserver.Controllers.Websocket.MasterWebsocketController import MasterWebsocketController


class UtilController(BaseHandler):

    def get(self, url):
        if url == "get_log_files":
            self.write(self.get_log_files())
        elif url == "get_log_file":
            self.write(self.get_log_file(urllib.parse.unquote(self.get_argument("file"))))
        elif url == "check_update":
            # should check slave version
            self.write(to_JSON(UpdateAvailable(Updater().check_version(), Updater().last_version)))

    def post(self, url):
        if url == "shutdown":
            self.shutdown()
        elif url == "restart_pi":
            self.restart_pi()
        elif url == "log":
            self.log()
        elif url == "update":
            instance = int(self.get_argument("instance"))
            if MasterWebsocketController().is_self(instance):
                Updater().update()
            else:
                MasterWebsocketController().send_to_slave(instance, "updater", "update", [])

    def log(self):
        Logger().write(LogVerbosity.Important, "============== Test ===============")
        EventManager.throw_event(EventType.Log, [])
        Logger().write(LogVerbosity.Important, "-- Threads --")
        for thread_list in sorted(ThreadManager.thread_history.values(), key=lambda x: len(x), reverse=True):
            Logger().write(LogVerbosity.Important, "     " + thread_list[0].thread_name + " " + str(len(thread_list)) + " entries, averages " + str(sum(c.end_time - c.start_time for c in thread_list if c.end_time != 0) / len(thread_list)) + "ms")
            for thread in [x for x in thread_list if x.end_time == 0]:
                Logger().write(LogVerbosity.Important, "         Currently running for " + str((current_time() - thread.start_time)/1000) + " seconds")

    def get_log_files(self):
        log_files = Logger().get_log_files()
        return to_JSON([(name, path, write_size(size)) for name, path, size in log_files])

    def get_log_file(self, file):
        return Logger().get_log_file(urllib.parse.unquote(file))

    def shutdown(self):
        Logger().write(LogVerbosity.Important, "Shutdown")
        os.system('sudo shutdown now')

    def restart_pi(self):
        Logger().write(LogVerbosity.Important, "Restart")
        os.system('sudo reboot')


class UpdateAvailable:

    def __init__(self, available, hash):
        self.available = available
        self.hash = hash