import traceback

import tornado.web

from Shared.Logger import Logger
from Shared.Util import to_JSON


class AuthController(tornado.web.RequestHandler):
    async def post(self, url):
        if self.get_argument("p") == "123":
            self.write(to_JSON(AuthResult(True, "123")))
        else:
            self.write(to_JSON(AuthResult(False, None)))

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

class AuthResult:

    def __init__(self, success, key):
        self.success = success
        self.key = key