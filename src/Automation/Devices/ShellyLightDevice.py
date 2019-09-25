import json
import socket

from Automation.DeviceBase import LightDevice
from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory
from Shared.Threading import CustomThread


class ShellyLightDevice(LightDevice):

    def __init__(self, id, name, ip_address, testing):
        super().__init__("ShellyLight", id, name, testing, True, None)
        self.ip_address = ip_address
        self.__port = 50000 + int(self.ip_address.split('.')[-1])
        self.__listen_socket_on = None
        self.__listen_socket_off = None
        self.__listen_thread_on = None
        self.__listen_thread_off = None

    def initialize(self):
        state = self.get_state()
        if self.testing:
            return True

        if state is None:
            return False

        self.on = state
        self.set_settings()
        self.listen()
        return True

    def deinitialize(self):
        # might need to implement this at some point
        pass

    def update(self, state, dim, warmth):
        self.on = state

    def get_state(self):
        if self.testing:
            return True

        result = RequestFactory.make_request("http://" + self.ip_address + "/relay/0")
        if result is None:
            Logger().write(LogVerbosity.Info, "Failed to get shelly light state")
            return None

        json_data = json.loads(result)
        return json_data["ison"]

    def set_on(self, state, src):
        if not self.testing:
            on_state = "on" if state else "off"
            RequestFactory.make_request("http://" + self.ip_address + "/relay/0?state=" + on_state, "POST")

        self.on = state
        Database().add_action_history(self.id, "on", src, state)

    def __set_on(self, value):
        Logger().write(LogVerbosity.Debug, self.name + " received device change. New state: " + str(value))
        self.on = value

    def set_settings(self):
        on_url = "192.168.2.100:" + str(self.__port)
        off_url = "192.168.2.100:" + str(self.__port + 100)
        settings = "http://" + self.ip_address + "/settings/relay/0?btn_on_url=" + on_url + "&out_on_url=" + on_url + "&btn_off_url=" + off_url + "&out_off_url=" + off_url
        Logger().write(LogVerbosity.Debug, self.name + " setting: " + settings)
        RequestFactory.make_request(settings, "POST")

    def listen(self):
        self.__listen_socket_on = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__listen_socket_on.bind(('localhost', self.__port))
        self.__listen_socket_off = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__listen_socket_off.bind(('localhost', self.__port + 100))
        self.__listen_thread_on = CustomThread(self.start_server, "Shelly on listener", [self.__listen_socket_on, lambda: self.__set_on(True)])
        self.__listen_thread_off = CustomThread(self.start_server, "Shelly off listener", [self.__listen_socket_off, lambda: self.__set_on(False)])
        self.__listen_thread_on.start()
        self.__listen_thread_off.start()

    def start_server(self, socket, on_receive):
        socket.listen(1)
        while True:
            connection, client_address = socket.accept()
            on_receive()
            connection.close()
