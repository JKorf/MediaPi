from Automation.DeviceBase import LightDevice


class TradfriLightDevice(LightDevice):

    def __init__(self, gateway, api, id, name, can_dim, can_change_warmth):
        super().__init__(id, name)
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

    def set_on(self, state):
        if self.testing:
            self.on = state
            return

        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.light_control.set_state(state))
        self.on = state

    def set_dimmer(self, value):
        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.light_control.set_dimmer(value))

    def set_warmth(self, value):
        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.light_control.set_color_temp(value))


class Obj:

    def __init__(self):
        pass