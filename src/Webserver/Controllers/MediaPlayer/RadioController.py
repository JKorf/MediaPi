from Shared.Logger import Logger
from Shared.Util import to_JSON
from Webserver.BaseHandler import BaseHandler
from Webserver.Providers.RadioProvider import RadioProvider


class RadioController(BaseHandler):
    def get(self, url):
        if url == "get_radios":
            Logger.write(2, "Get radio list")
            self.write(to_JSON(RadioProvider.get_list()))
