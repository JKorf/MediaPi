import os
import urllib.parse
import urllib.request

from Automation.LightManager import LightManager
from Shared.Events import EventManager
from Shared.Events import EventType
from Shared.Logger import Logger
from Shared.Settings import Settings as AppSettings
from Shared.Stats import Stats
from Shared.Threading import ThreadManager
from Shared.Util import to_JSON, RequestFactory, current_time, write_size
from WebServer.Models import Info, StartUp


class UtilController:

    @staticmethod
    def info():
        info = Info(current_time() - Stats.total('start_time'), Stats.total('peers_connect_try'), Stats.total('peers_connect_failed'), Stats.total('peers_connect_success'),
                    Stats.total('peers_source_dht'), Stats.total('peers_source_udp_tracker'), Stats.total('peers_source_http_tracker'), Stats.total('peers_source_exchange'),
                    write_size(Stats.total('total_downloaded')), Stats.total('threads_started'), Stats.total('subs_downloaded'), Stats.total('vlc_played'),
                    write_size(Stats.total('max_download_speed')), Stats.total('peers_source_dht_connected'), Stats.total('peers_source_udp_tracker_connected'), Stats.total('peers_source_http_tracker_connected'), Stats.total('peers_source_pex_connected'))

        return to_JSON(info)

    @staticmethod
    async def get_protected_img(url):
        try:
            result = await RequestFactory.make_request_async(url)
            if not result:
                Logger.write(2, "Couldnt get image: " + urllib.parse.unquote(url))
                result = open(os.getcwd() + "/Interface/Mobile/Images/unknown.png", "rb").read()
        except Exception:
            result = open(os.getcwd() + "/Interface/Mobile/Images/noimage.png", "rb").read()
        return result

    @staticmethod
    def test():
        Logger.write(2, "============== Test ===============")
        EventManager.throw_event(EventType.Log, [])
        with Logger.lock:
            Logger.write(3, "-- Threads --")
            for thread in ThreadManager.threads:
                Logger.write(3, "     " + thread.thread_name + ", running for " + str((current_time() - thread.start_time)/1000) + " seconds")

    @staticmethod
    def shutdown():
        Logger.write(3, "Shutdown")
        os.system('sudo shutdown now')

    @staticmethod
    def restart_pi():
        Logger.write(3, "Restart")
        os.system('sudo reboot')

    @staticmethod
    def startup():
        return to_JSON(
            StartUp(AppSettings.get_string("name"), LightManager().enabled))