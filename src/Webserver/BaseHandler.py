import traceback

import tornado.web

from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings


class BaseHandler(tornado.web.RequestHandler):
    def prepare(self):
        if self.request.method == "GET" or self.request.method == "POST":
            key = self.request.headers.get('Auth-Key', None)
            Logger.write(2, "KEY RECEIVED: " + str(key))

            #self.send_error(401)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Auth-Key")

    def _handle_request_exception(self, e):
        Logger.write(3, "Error in Tornado requests: " + str(e), 'error')
        stack_trace = traceback.format_exc().split('\n')
        for stack_line in stack_trace:
            Logger.write(3, stack_line)
        self.set_status(503)
        self.finish(str(e))

    def options(self, *args, **kwargs):
        self.set_status(200)

    @staticmethod
    async def request_master_async(url):
        reroute = str(Settings.get_string("master_ip")) + url
        Logger.write(2, "Sending request to master at " + reroute)
        return await RequestFactory.make_request_async(reroute, "GET")