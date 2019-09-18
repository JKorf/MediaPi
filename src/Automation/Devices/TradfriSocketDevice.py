from Automation.DeviceBase import SwitchDevice
from Database.Database import Database


class TradfriSocketDevice(SwitchDevice):

    def __init__(self, gateway, api, id, name, testing):
        super().__init__("TradfriSocket", id, name, testing, False)
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

    def set_active(self, state, src):
        if self.testing:
            self.active = state
            Database().add_action_history(self.id, "active", src, state)
            return

        device = self.__api(self.__gateway.get_device(self.id))
        self.__api(device.socket_control.set_state(state))
        Database().add_action_history(self.id, "active", src, state)
        self.active = state
