import random
import time

from Automation.DeviceBase import SwitchDevice
from Database.Database import Database
from Shared.Logger import LogVerbosity, Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time


class TradfriSocketDevice(SwitchDevice):

    def __init__(self, gateway, api, id, name, testing):
        super().__init__("TradfriSocket", id, name, testing, False)
        self.__gateway = gateway
        self.__api = api
        self.__observe_thread = None
        self.__device = None

    def initialize(self):
        self.active = self.get_state()
        self.start_observing()

    def update(self, state):
        self.active = state

    def set_name(self, name):
        if self.testing:
            self.name = name
            return

        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.set_name(name))
        self.name = name

    def get_state(self):
        if self.testing:
            return False

        self.__device = self.__api(self.__gateway.get_device(self.id))
        return self.__device.state

    def set_active(self, state, src):
        if self.testing:
            self.active = state
            Database().add_action_history(self.id, "active", src, state)
            return

        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.socket_control.set_state(state))
        Database().add_action_history(self.id, "active", src, state)
        self.active = state

    def start_observing(self):
        if self.testing:
            self.__observe_thread = CustomThread(self.random_change, "Socket device changer", [])
            self.__observe_thread.start()
            return

        Logger().write(LogVerbosity.All, "(Re)starting observe for device " + self.name)

        self.__observe_thread = CustomThread(lambda: self.__api(self.__device.observe(
            self.device_change,
            lambda x: self.start_observing(), duration=60)), "Light device observer", [])
        self.__observe_thread.start()

    def device_change(self, device):
        Logger().write(LogVerbosity.Debug, "Tradfri socket change received. New state: " + str(device.socket_control.sockets[0].state))
        self.active = device.socket_control.sockets[0].state

    def random_change(self):
        while True:
            self.active = bool(random.getrandbits(1))
            time.sleep(random.randint(5, 30))