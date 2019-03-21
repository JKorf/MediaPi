import base64
import hashlib
import hmac
from threading import Lock, Event

from flask import Flask
from flask import request
from flask_cors import CORS
from flask_socketio import SocketIO
import logging

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Observable import Observable
from Shared.Settings import Settings, SecureSettings
from Shared.Threading import CustomThread
from Shared.Util import Singleton


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app)


class APIController(metaclass=Singleton):

    salt = None
    slaves = None
    last_id = 1
    last_id_lock = Lock()
    last_data = dict()

    def __init__(self):
        self.slave = Settings.get_bool("slave")

    def start(self):
        APIController.slaves = SlaveCollection()

        log_verbosity = Settings.get_int("log_level")
        if log_verbosity > 0:
            flask_logger = logging.getLogger('werkzeug')
            flask_logger.setLevel(logging.INFO)

        if Settings.get_bool("slave"):
            thread = CustomThread(self.internal_start_slave, "API controller", [])
            thread.start()
        else:
            thread = CustomThread(self.internal_start_master, "API controller", [])
            thread.start()

    def internal_start_master(self):
        from Webserver.Controllers.AuthController import AuthController
        from Webserver.Controllers.MediaPlayer.MovieController import MovieController
        from Webserver.Controllers.MediaPlayer.ShowController import ShowController
        from Webserver.Controllers.MediaPlayer.PlayController import PlayController
        from Webserver.Controllers.MediaPlayer.HDController import HDController
        from Webserver.Controllers.MediaPlayer.RadioController import RadioController
        from Webserver.Controllers.MediaPlayer.TorrentController import TorrentController
        from Webserver.Controllers.DataController import DataController
        from Webserver.Controllers.LightController import LightController
        from Webserver.Controllers.ToonController import ToonController
        from Webserver.Controllers.UtilController import UtilController
        from Webserver.Controllers.Websocket2.UIWebsocketController import UIWebsocketController
        from Webserver.Controllers.Websocket2.SlaveWebsocketController import SlaveWebsocketController

        UIWebsocketController.init()
        SlaveWebsocketController.init()
        APIController.slaves.add_slave(SlaveClient(1, Settings.get_string("name"), None))

        socketio.run(app, host='0.0.0.0', port=int(Settings.get_string("api_port")), log_output=True)

    @staticmethod
    def internal_start_slave():
        from Webserver.Controllers.Websocket2.SlaveClientController import SlaveClientController

        SlaveClientController.init()
        SlaveClientController.connect()

    @staticmethod
    @app.before_request
    def before_req():
        if request.method == "OPTIONS" \
                or request.path.startswith("/auth/") \
                or request.path.startswith("/ws")\
                or request.path.startswith("/Slave"):
            return

        session_key = request.headers.get('Session-Key', None)
        client_id = request.headers.get('Client-ID', None)
        if session_key is None or client_id is None:
            Logger().write(LogVerbosity.Info, "Request without session key or client id")
            return "Auth failed", 401

        client_key = APIController.get_salted(client_id)
        result = Database().check_session_key(client_key, session_key)
        if not result:
            Logger().write(LogVerbosity.Info, "Request with invalid client id / session key")
            return "Auth failed", 401

    @staticmethod
    @app.errorhandler(500)
    def handle_internal_server_error(e):
        Logger().write_error(e, "Error in API request")
        return str(e), 500

    @staticmethod
    def get_salt():
        if APIController.salt is None:
            APIController.salt = SecureSettings.get_string("api_salt").encode()
        return APIController.salt

    @staticmethod
    def get_salted(client_id):
        dig = hmac.new(APIController.get_salt(), msg=client_id.encode(), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    @staticmethod
    def next_id():
        with APIController.last_id_lock:
            APIController.last_id += 1
            return APIController.last_id

    def ui_request(self, topic, callback, timeout, args):
        from Webserver.Controllers.Websocket2.UIWebsocketController import UIWebsocketController
        from Webserver.Controllers.Websocket2.SlaveClientController import SlaveClientController

        if self.slave:
            SlaveClientController.request_ui_cb(topic, callback, timeout, args)
        else:
            UIWebsocketController.request_cb(topic, callback, timeout, args)


class SlaveClient:

    def __init__(self, slave_id, name, client):
        self.id = slave_id
        self.name = name
        self._client = client
        self.last_seen = 0
        self._data_registrations = dict()
        self._data_registrations["player"] = None
        self._data_registrations["media"] = None
        self._data_registrations["torrent"] = None
        self._data_registrations["state"] = None
        self._data_registrations["stats"] = None
        self._data_registrations["update"] = None

    def update_data(self, name, data):
        self._data_registrations[name].data = data

    def get_data(self, name):
        return self._data_registrations[name].data


class SlaveCollection(Observable):

    def __init__(self):
        super().__init__("slaves", 1)
        self.data = []

    def add_slave(self, slave):
        self.data.append(slave)
        self.changed()

    def remove_slave(self, slave):
        self.data.remove(slave)
        self.changed()

    def get_slave(self, name):
        slave = [x for x in self.data if x.name == name]
        if len(slave) > 0:
            return slave[0]
        return None

    def get_slave_by_id(self, slave_id):
        slave = [x for x in self.data if x.id == slave_id]
        if len(slave) > 0:
            return slave[0]
        return None

    def get_slave_by_sid(self, sid):
        slave = [x for x in self.data if x._client is not None and x._client.sid == sid]
        if len(slave) > 0:
            return slave[0]
        return None


class WebsocketClient:

    def __init__(self, sid, connect_time):
        self.sid = sid
        self.connect_time = connect_time
        self.authenticated = False


class Request:

    def __init__(self, request_id, topic, data, on_complete):
        self.evnt = Event()
        self.request_id = request_id
        self.topic = topic
        self.data = data
        self.response = None
        self.on_complete = on_complete

    def wait(self, timeout):
        if not self.evnt.wait(timeout):
            self.on_complete(self)
        return self.response

    def set(self, data):
        self.response = data
        self.on_complete(self)
        self.evnt.set()
