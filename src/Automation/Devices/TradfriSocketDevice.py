from Automation.DeviceBase import SwitchDevice


class TradfriSocketDevice(SwitchDevice):

    def __init__(self, gateway, api, id, name):
        super().__init__(id, name)
        self.__gateway = gateway
        self.__api = api

    def initialize(self):
        self.active = self.get_state()

    def update(self, state):
        self.active = state

    def get_state(self):
        if self.testing:
            return False

        return self.__api(self.__gateway.get_device(self.id)).state

    def set_active(self, state):
        if self.testing:
            self.active = state
            return

        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.socket_control.set_state(state))
        self.active = state
