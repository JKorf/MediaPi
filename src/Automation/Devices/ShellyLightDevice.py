import json

from Automation.DeviceBase import LightDevice
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory


class ShellyLightDevice(LightDevice):

    def __init__(self, id, name, ip_address):
        super().__init__(id, name)
        self.ip_address = ip_address

    def initialize(self):
        self.on = self.get_state()

    def update(self, state, dim, warmth):
        self.on = state

    def get_state(self):
        if self.testing:
            return True

        result = RequestFactory.make_request("http://" + self.ip_address + "/relay/0")
        if result is None:
            Logger().write(LogVerbosity.Warning, "Failed to get shelly light state")

        json_data = json.loads(result)
        return json_data["ison"]

    def set_on(self, state):
        if not self.testing:
            on_state = "on" if state else "off"
            RequestFactory.make_request("http://" + self.ip_address + "/relay/0?state=" + on_state, "POST")

        self.on = state
