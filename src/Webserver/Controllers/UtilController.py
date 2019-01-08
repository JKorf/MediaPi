import os
import urllib.parse
import urllib.request

from Controllers.LightController import LightManager
from MediaPlayer.MediaPlayer import MediaManager
from Shared.Events import EventManager
from Shared.Events import EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
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
        elif url == "get_subtitles":
            data = MediaManager().subtitle_provider.search_subtitles_for_file(self.get_argument("path"), self.get_argument("file"))
            self.write(to_JSON(data))

    def post(self, url):
        if url == "shutdown":
            self.shutdown()
        elif url == "restart_pi":
            self.restart_pi()
        elif url == "test":
            self.test()

    def info(self):
        info = Info(current_time() - Stats.total('start_time'), Stats.total('peers_connect_try'), Stats.total('peers_connect_failed'), Stats.total('peers_connect_success'),
                    Stats.total('peers_source_dht'), Stats.total('peers_source_udp_tracker'), Stats.total('peers_source_http_tracker'), Stats.total('peers_source_exchange'),
                    write_size(Stats.total('total_downloaded')), Stats.total('subs_downloaded'), Stats.total('vlc_played'),
                    write_size(Stats.total('max_download_speed')), Stats.total('peers_source_dht_connected'), Stats.total('peers_source_udp_tracker_connected'), Stats.total('peers_source_http_tracker_connected'),
                    Stats.total('peers_source_pex_connected'))

        return to_JSON(info)

    async def get_protected_img(self, url):
        try:
            result = await RequestFactory.make_request_async(url)
            if not result:
                Logger.write(2, "Couldnt get image: " + urllib.parse.unquote(url))
                result = open(os.getcwd() + "/Interface/Mobile/Images/unknown.png", "rb").read()
        except Exception:
            result = open(os.getcwd() + "/Interface/Mobile/Images/noimage.png", "rb").read()
        return result

    def test(self):
        Logger.write(2, "============== Test ===============")
        EventManager.throw_event(EventType.Log, [])
        with Logger.lock:
            Logger.write(3, "-- Threads --")
            for thread in ThreadManager.threads:
                Logger.write(3, "     " + thread.thread_name + ", running for " + str((current_time() - thread.start_time)/1000) + " seconds")

    def shutdown(self):
        Logger.write(3, "Shutdown")
        os.system('sudo shutdown now')

    def restart_pi(self):
        Logger.write(3, "Restart")
        os.system('sudo reboot')

    def startup(self):
        return to_JSON(
            StartUp(AppSettings.get_string("name"), LightManager().enabled))
