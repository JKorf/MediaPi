import sys
from enum import Enum

from Shared.Observable import Observable


class Device(Observable):

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if not name.startswith("_") and hasattr(self, "changed"):
            if self.changed is not None:
                self.changed()

    def __init__(self, device_type, id, name):
        super().__init__(id, 0.5)
        self.device_type = device_type
        self.name = name
        self.id = id
        self.testing = sys.platform != "linux" and sys.platform != "linux2"


class LightDevice(Device):

    def __init__(self, id, name):
        super().__init__(DeviceType.Light, id, name)
        self.on = False

        self.can_dim = False
        self.can_change_warmth = False

        self.dim = 0
        self.warmth = 0

    def set_on(self, on):
        raise NotImplementedError("On command not implemented on light device " + self.name)

    def set_dimmer(self, dim):
        if not self.can_dim:
            raise NotImplementedError("Can't dim on light device " + self.name)

    def set_warmth(self, warmth):
        if not self.can_change_warmth:
            raise NotImplementedError("Can't change warmth on light device " + self.name)

    def update(self, on, dim, warmth):
        raise NotImplementedError("Update command not implemented on light device " + self.name)


class ThermostatDevice(Device):

    def __init__(self, id, name):
        super().__init__(DeviceType.Thermostat, id, name)
        self.temperature = 0

    def set_setpoint(self, temperature):
        raise NotImplementedError("Set setpoint command not implemented on thermostat device " + self.name)

    def update(self, temperature, setpoint):
        raise NotImplementedError("Update command not implemented on thermostat device " + self.name)


class SwitchDevice(Device):

    def __init__(self, id, name):
        super().__init__(DeviceType.Switch, id, name)
        self.active = False

    def set_active(self, active):
        raise NotImplementedError("Set active command not implemented on switch device " + self.name)

    def update(self, active):
        raise NotImplementedError("Update command not implemented on switch device " + self.name)


class DeviceType(Enum):
    Light = "Light"
    Switch = "Switch"
    Vacuum = "Vacuum"
    Thermostat = "Thermostat"
    Sensor = "Sensor"

