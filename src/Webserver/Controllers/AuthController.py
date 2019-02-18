import base64
import hashlib
import hmac
import traceback

import tornado.web

from Database.Database import Database
from Shared.Logger import Logger
from Shared.Util import to_JSON


class AuthController(tornado.web.RequestHandler):

    async def post(self, url):
        success, key = self.validate(self.get_argument("i"), self.get_argument("p"))
        self.write(to_JSON(AuthResult(success, key)))

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

    def validate(self, id, p):
        if p == "123":
            key = self.generate_key(id, p)
            Database().add_client(id, key)
            return True, key

        return False, None

    def generate_key(self, id, p):
        dig = hmac.new(p.encode('utf-8'), msg=id.encode('utf-8'), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()


class AuthResult:

    def __init__(self, success, key):
        self.success = success
        self.key = key