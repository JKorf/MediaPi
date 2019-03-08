import base64
import hashlib
import hmac
import traceback
import uuid

import tornado.web

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import SecureSettings
from Shared.Util import to_JSON


class AuthController(tornado.web.RequestHandler):

    salt = None

    @staticmethod
    def get_salt():
        if AuthController.salt is None:
            AuthController.salt = SecureSettings.get_string("api_salt").encode()
        return AuthController.salt

    async def post(self, url):
        if url == "login":
            client_id = self.request.headers.get('Client-ID', None)
            p = self.get_argument("p")
            success, key = self.validate(client_id, p)
            self.write(to_JSON(AuthResult(success, key)))
            if not success:
                self.set_status(401)
            Logger().write(LogVerbosity.Info, str(client_id) + " log on result: " + str(success))

        elif url == "refresh":
            client_id = self.request.headers.get('Client-ID', None)
            client_key = self.get_salted(client_id)
            client_known = Database().check_client_key(client_key)
            if not client_known:
                self.write(to_JSON(AuthResult(False, None)))
                Logger().write(LogVerbosity.Info, str(client_id) + " failed to refresh")
                self.set_status(401)
                return

            session_key = self.generate_session_key()
            Database().refresh_session_key(client_key, session_key)
            self.write(to_JSON(AuthResult(True, session_key)))
            Logger().write(LogVerbosity.Debug, str(client_id) + " successfully refreshed")

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Client-ID, Session-Key")

    def _handle_request_exception(self, e):
        Logger().write(LogVerbosity.Important, "Error in Tornado requests: " + str(e), 'error')
        stack_trace = traceback.format_exc().split('\n')
        for stack_line in stack_trace:
            Logger().write(LogVerbosity.Important, stack_line)
        self.set_status(503)
        self.finish(str(e))

    def options(self, url):
        self.set_status(200)

    def validate(self, id, p):
        if self.get_salted(p) == SecureSettings.get_string("api_password"):
            client_key = self.get_salted(id)
            session_key = self.generate_session_key()
            Database().add_client(client_key, session_key)
            return True, session_key

        return False, None

    @staticmethod
    def get_salted(client_id):
        dig = hmac.new(AuthController.get_salt(), msg=client_id.encode(), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    @staticmethod
    def generate_session_key():
        return uuid.uuid4().hex


class AuthResult:

    def __init__(self, success, key):
        self.success = success
        self.key = key