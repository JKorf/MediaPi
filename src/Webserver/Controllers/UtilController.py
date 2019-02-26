import os
import urllib.parse

from Controllers.LightManager import LightManager
from Shared.Events import EventManager
from Shared.Events import EventType
from Shared.Logger import Logger
from Shared.Settings import Settings as AppSettings
from Shared.Stats import Stats
from Shared.Threading import ThreadManager
from Shared.Util import to_JSON, current_time, write_size
from Webserver.Models import Info, StartUp
from Webserver.BaseHandler import BaseHandler


class UtilController(BaseHandler):

    async def get(self, url):
        if url == "startup":
            self.write(self.startup())
        elif url == "info":
            self.write(self.info())
        elif url == "get_log_files":
            self.write(self.get_log_files())
        elif url == "get_log_file":
            self.write(self.get_log_file(urllib.parse.unquote(self.get_argument("file"))))

    def post(self, url):
        if url == "shutdown":
            self.shutdown()
        elif url == "restart_pi":
            self.restart_pi()
        elif url == "log":
            self.log()

    def info(self):
        info = Info(current_time() - Stats.total('start_time'), Stats.total('peers_connect_try'), Stats.total('peers_connect_failed'), Stats.total('peers_connect_success'),
                    Stats.total('peers_source_dht'), Stats.total('peers_source_udp_tracker'), Stats.total('peers_source_http_tracker'), Stats.total('peers_source_exchange'),
                    write_size(Stats.total('total_downloaded')), Stats.total('subs_downloaded'), Stats.total('vlc_played'),
                    write_size(Stats.total('max_download_speed')), Stats.total('peers_source_dht_connected'), Stats.total('peers_source_udp_tracker_connected'), Stats.total('peers_source_http_tracker_connected'),
                    Stats.total('peers_source_pex_connected'))

        return to_JSON(info)

    def log(self):
        Logger.write(2, "============== Test ===============")
        EventManager.throw_event(EventType.Log, [])
        with Logger.lock:
            Logger.write(3, "-- Threads --")
            for thread_list in sorted(ThreadManager.thread_history.values(), key=lambda x: len(x), reverse=True):
                Logger.write(3, "     " + thread_list[0].thread_name + " " + str(len(thread_list)) + " entries, averages " + str(sum(c.end_time - c.start_time for c in thread_list if c.end_time != 0) / len(thread_list)) + "ms")
                for thread in [x for x in thread_list if x.end_time == 0]:
                    Logger.write(3, "         Currently running for " + str((current_time() - thread.start_time)/1000) + " seconds")

    def get_log_files(self):
        log_files = Logger.get_log_files()
        return to_JSON([(name, write_size(size)) for name, size in log_files])

    def get_log_file(self, file):
        return Logger.get_log_file(file)

    def shutdown(self):
        Logger.write(3, "Shutdown")
        os.system('sudo shutdown now')

    def restart_pi(self):
        Logger.write(3, "Restart")
        os.system('sudo reboot')

    def startup(self):
        return to_JSON(
            StartUp(AppSettings.get_string("name"), LightManager().enabled))
