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
        ip_addr = request.headers.get('HTTP_X_FORWARDED_FOR', None) or request.remote_addr
        user_agent = request.user_agent.string
        success, key = AuthController.validate(client_id, p, ip_addr, user_agent)

        Logger().write(LogVerbosity.Info, str(client_id) + " log on result: " + str(success))

        status = 200
        if not success:
            Database().add_login_attempt(APIController.get_salted(client_id), ip_addr, user_agent, "Login")
            status = 401
        return to_JSON(AuthResult(success, key)), status

    @staticmethod
    @app.route('/auth/refresh', methods=['POST'])
    def refresh():
        client_id = request.headers.get('Client-ID', None)
        client_key = APIController.get_salted(client_id)
        client_known = Database().client_known(client_key)
        ip_addr = request.headers.get('HTTP_X_FORWARDED_FOR', None) or request.remote_addr
        user_agent = request.user_agent.string

        if not client_known:
            Logger().write(LogVerbosity.Info, str(client_id) + " failed to refresh")
            Database().add_login_attempt(client_key, ip_addr, user_agent, "Refresh")
            return to_JSON(AuthResult(False, None)), 401

        session_key = AuthController.generate_session_key()
        Database().refresh_session_key(client_key, session_key, ip_addr, user_agent)
        Logger().write(LogVerbosity.Debug, str(client_id) + " successfully refreshed")
        return to_JSON(AuthResult(True, session_key)), 200

    @staticmethod
    def validate(client_id, p, ip, user_agent):
        if APIController.get_salted(p) == SecureSettings.get_string("api_password"):
            client_key = APIController.get_salted(client_id)
            session_key = AuthController.generate_session_key()
            Database().add_client(client_key, session_key, ip, user_agent)
            return True, session_key

        return False, None

    @staticmethod
    def generate_session_key():
        return uuid.uuid4().hex


class AuthResult:

    def __init__(self, success, key):
        self.success = success
        self.key = key
