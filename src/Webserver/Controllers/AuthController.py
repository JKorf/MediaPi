import base64
import hashlib
import hmac
import uuid

from flask import request

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import SecureSettings
from Shared.Util import to_JSON
from Webserver.APIController import app, APIController


class AuthController:

    @staticmethod
    @app.route('/auth/login', methods=['POST'])
    def login():
        client_id = request.headers.get('Client-ID', None)
        p = request.args.get('p')
        success, key = AuthController.validate(client_id, p)

        Logger().write(LogVerbosity.Info, str(client_id) + " log on result: " + str(success))

        status = 200
        if not success:
            status = 401
        return to_JSON(AuthResult(success, key)), status

    @staticmethod
    @app.route('/auth/refresh', methods=['POST'])
    def refresh():
        client_id = request.headers.get('Client-ID', None)
        client_key = APIController.get_salted(client_id)
        client_known = Database().check_client_key(client_key)
        if not client_known:
            Logger().write(LogVerbosity.Info, str(client_id) + " failed to refresh")
            return to_JSON(AuthResult(False, None)), 401

        session_key = AuthController.generate_session_key()
        Database().refresh_session_key(client_key, session_key)
        Logger().write(LogVerbosity.Debug, str(client_id) + " successfully refreshed")
        return to_JSON(AuthResult(True, session_key)), 200

    @staticmethod
    def validate(id, p):
        if APIController.get_salted(p) == SecureSettings.get_string("api_password"):
            client_key = APIController.get_salted(id)
            session_key = AuthController.generate_session_key()
            Database().add_client(client_key, session_key)
            return True, session_key

        return False, None

    @staticmethod
    def generate_session_key():
        return uuid.uuid4().hex


class AuthResult:

    def __init__(self, success, key):
        self.success = success
        self.key = key