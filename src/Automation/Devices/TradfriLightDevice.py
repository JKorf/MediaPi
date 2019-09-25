import math
import random
import time

from Automation.DeviceBase import LightDevice
from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread


class TradfriLightDevice(LightDevice):

    def __init__(self, gateway, api, provider_name, id, name, testing, can_dim, can_change_warmth):
        super().__init__("TradfriLight", id, name, testing, False, provider_name)
        self.__gateway = gateway
        self.__api = api
        self.can_dim = can_dim
        self.can_change_warmth = can_change_warmth
        self.__observe_thread = None
        self.__device = None
        self.__running = False

    def initialize(self):
        state = self.get_state()
        if state is None:
            return False

        self.__running = True
        self.on = state.state
        self.dim = state.dimmer
        self.warmth = state.color_temp
        self.start_observing()
        return True

    def deinitialize(self):
        self.__running = False
        if self.__observe_thread:
            self.__observe_thread.join()

    def get_state(self):
        if self.testing:
            result = Obj()
            result.state = False
            result.dimmer = 50
            result.color_temp = 25
            return result

        try:
            self.__device = self.__api(self.__gateway.get_device(self.id))
            return self.__device.light_control.lights[0]
        except:
            return None

    def update(self, state, dim, warmth):
        self.on = state
        self.dim = dim
        self.warmth = warmth

    def set_name(self, name):
        if self.testing:
            self.name = name
            return

        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.set_name(name))
        self.name = name

    def set_on(self, state, src):
        if self.testing:
            Database().add_action_history(self.id, "on", src, state)
            self.on = state
            return

        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.light_control.set_state(state))
        Database().add_action_history(self.id, "on", src, state)
        self.on = state

    def set_dim(self, value, src):
        if self.testing:
            self.dim = value
            return

        tradfri_value = math.floor(value / 100 * 254)
        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.light_control.set_dimmer(tradfri_value))
        Logger().write(LogVerbosity.Debug, "Set dim value of " + str(self.name) + " to " + str(tradfri_value))
        Database().add_action_history(self.id, "dim", src, value)
        self.dim = value

    def set_warmth(self, value, src):
        if self.testing:
            self.warmth = value
            return

        tradfri_value = math.floor(value / 100 * 204 + 250)
        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.light_control.set_color_temp(tradfri_value))
        Logger().write(LogVerbosity.Debug, "Set warmth value of " + str(self.name) + " to " + str(tradfri_value))
        Database().add_action_history(self.id, "warmth", src, value)
        self.warmth = value

    def start_observing(self):
        if self.testing:
            self.__observe_thread = CustomThread(self.random_change, "Light device changer", [])
            self.__observe_thread.start()
            return

        if not self.__running:
            return

        Logger().write(LogVerbosity.All, "(Re)starting observe for device " + self.name)

        self.__observe_thread = CustomThread(lambda: self.__api(self.__device.observe(
            self.device_change,
            lambda x: self.start_observing(), duration=30)), "Light device observer", [])
        self.__observe_thread.start()

    def device_change(self, device):
        Logger().write(LogVerbosity.Debug,
                       "Tradfri light change received. New state: " + str(device.light_control.lights[0].state))
        self.on = device.light_control.lights[0].state
        self.dim = device.light_control.lights[0].dimmer
        self.warmth = device.light_control.lights[0].color_temp

    def random_change(self):
        while self.__running:
            self.on = bool(random.getrandbits(1))
            time.sleep(random.randint(5, 30))


class Obj:

    def __init__(self):
        pass