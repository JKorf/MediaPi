import traceback

import tornado.web

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Webserver.Controllers.AuthController import AuthController


class BaseHandler(tornado.web.RequestHandler):
    def prepare(self):
        if self.request.method == "GET" or self.request.method == "POST":
            session_key = self.request.headers.get('Session-Key', None)
            client_id = self.request.headers.get('Client-ID', None)
            if session_key is None or client_id is None:
                Logger().write(LogVerbosity.Info, "Request without session key or client id")
                self.send_error(401)
                return

            client_key = AuthController.get_salted(client_id)
            result = Database().check_session_key(client_key, session_key)
            if not result:
                Logger().write(LogVerbosity.Info, "Request with invalid client id / session key")
                self.send_error(401)
                return

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Client-ID, Session-Key")

    def _handle_request_exception(self, e):
        Logger().write_error(e, "Exception in UI request")
        self.set_status(503)
        self.finish(str(e))

    def options(self, *args, **kwargs):
        self.set_status(200)

    @staticmethod
    async def request_master_async(url):
        reroute = str(Settings.get_string("master_ip")) + url
        Logger().write(LogVerbosity.Debug, "Sending request to master at " + reroute)
        return await RequestFactory.make_request_async(reroute, "GET")