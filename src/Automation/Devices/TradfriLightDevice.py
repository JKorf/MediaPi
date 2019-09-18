from Automation.DeviceBase import LightDevice
from Database.Database import Database


class TradfriLightDevice(LightDevice):

    def __init__(self, gateway, api, id, name, testing, can_dim, can_change_warmth):
        super().__init__("TradfriLight", id, name, testing, False)
        self.__gateway = gateway
        self.__api = api
        self.can_dim = can_dim
        self.can_change_warmth = can_change_warmth

    def initialize(self):
        state = self.get_state()
        self.on = state.state
        self.dim = state.dimmer
        self.warmth = state.color_temp

    def get_state(self):
        if self.testing:
            result = Obj()
            result.state = False
            result.dimmer = 50
            result.color_temp = 25
            return result

        return self.__api(self.__gateway.get_device(self.id)).light_control.lights[0]

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

        tradfri_value = value / 100 * 254
        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.light_control.set_dimmer(tradfri_value))
        Database().add_action_history(self.id, "dim", src, value)
        self.dim = value

    def set_warmth(self, value, src):
        if self.testing:
            self.warmth = value
            return

        tradfri_value = value / 100 * 204 + 250
        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.light_control.set_color_temp(tradfri_value))
        Database().add_action_history(self.id, "warmth", src, value)
        self.warmth = value


class Obj:

    def __init__(self):
        pass