import random
import time

from Automation.DeviceBase import SwitchDevice
from Database.Database import Database
from Shared.Logger import LogVerbosity, Logger
from Shared.Threading import CustomThread


class TradfriSocketDevice(SwitchDevice):

    def __init__(self, gateway, api, provider_name, id, name, testing):
        super().__init__("TradfriSocket", id, name, testing, False, provider_name)
        self.__gateway = gateway
        self.__api = api
        self.__observe_thread = None
        self.__device = None
        self.__running = False

    def initialize(self):
        state = self.get_state()
        if state is None:
            return False
        self.active = state
        self.__running = True
        self.start_observing()
        return True

    def deinitialize(self):
        self.__running = False
        if self.__observe_thread:
            self.__observe_thread.join()

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

        try:
            self.__device = self.__api(self.__gateway.get_device(self.id))
            return self.__device.state
        except:
            return None

    def set_active(self, state, src):
        if self.testing:
            self.active = state
            Database().add_action_history(self.id, "active", src, state)
            return

        if not self.__running:
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
            lambda x: self.start_observing(), duration=30)), "Light device observer", [])
        self.__observe_thread.start()

    def device_change(self, device):
        Logger().write(LogVerbosity.Debug, "Tradfri socket change received. New state: " + str(device.socket_control.sockets[0].state))
        self.active = device.socket_control.sockets[0].state

    def random_change(self):
        while self.__running:
            self.active = bool(random.getrandbits(1))
            time.sleep(random.randint(5, 30))