from enum import Enum

from Shared.Observable import Observable


class Device(Observable):

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if not name.startswith("_") and hasattr(self, "changed"):
            if self.changed is not None:
                self.changed()

    def __init__(self, device_type, implementation_type, id, name, testing, is_base_device, provider_name):
        super().__init__(id, 0.5)
        self.device_type = device_type
        self.implementation_type = implementation_type
        self.name = name
        self.id = id
        self.testing = testing
        self.is_base_device = is_base_device
        self.provider_name = provider_name
        self.accessible = False

    def initialize(self):
        return True

    def deinitialize(self):
        pass

    def set_name(self, name):
        self.name = name


class LightDevice(Device):

    def __init__(self, implementation_type, id, name, testing, is_base_device, provider_name):
        super().__init__(DeviceType.Light, implementation_type, id, name, testing, is_base_device, provider_name)
        self.on = False

        self.can_dim = False
        self.can_change_warmth = False

        self.dim = 0
        self.warmth = 0

    def set_on(self, on, src):
        raise NotImplementedError("On command not implemented on light device " + self.name)

    def set_dim(self, dim, src):
        if not self.can_dim:
            raise NotImplementedError("Can't dim on light device " + self.name)

    def set_warmth(self, warmth, src):
        if not self.can_change_warmth:
            raise NotImplementedError("Can't change warmth on light device " + self.name)

    def update(self, on, dim, warmth):
        raise NotImplementedError("Update command not implemented on light device " + self.name)


class ThermostatDevice(Device):

    def __init__(self, implementation_type, id, name, testing, is_base_device, provider_name):
        super().__init__(DeviceType.Thermostat, implementation_type, id, name, testing, is_base_device, provider_name)
        self.temperature = 0

    def set_setpoint(self, temperature, src):
        raise NotImplementedError("Set setpoint command not implemented on thermostat device " + self.name)

    def update(self, temperature, setpoint):
        raise NotImplementedError("Update command not implemented on thermostat device " + self.name)


class SwitchDevice(Device):

    def __init__(self, implementation_type, id, name, testing, is_base_device, provider_name):
        super().__init__(DeviceType.Switch, implementation_type, id, name, testing, is_base_device, provider_name)
        self.active = False

    def set_active(self, active, src):
        raise NotImplementedError("Set active command not implemented on switch device " + self.name)

    def update(self, active):
        raise NotImplementedError("Update command not implemented on switch device " + self.name)


class DeviceProvider:

    def __init__(self, name, ip, type):
        self.name = name
        self.ip = ip
        self.type = type

    def init(self):
        raise NotImplementedError("Init not implemented in provider")

    def get_devices(self):
        raise NotImplementedError("Get devices not implemented in provider")


class DeviceType(Enum):
    Light = "Light"
    Switch = "Switch"
    Vacuum = "Vacuum"
    Thermostat = "Thermostat"
    Sensor = "Sensor"

