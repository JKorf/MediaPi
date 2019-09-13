import random

from Automation.DeviceBase import DeviceType
from Automation.Devices.ShellyLightDevice import ShellyLightDevice
from Automation.Devices.ToonThermostatDevice import ToonThermostatDevice
from Automation.TradfriManager import TradfriManager
from Shared.Observable import Observable
from Shared.Settings import SecureSettings
from Shared.Util import Singleton


class DeviceController(Observable, metaclass=Singleton):

    def __init__(self):
        super().__init__("DeviceData", 0.5)
        self.devices = []
        self.groups = []

    def initialize(self):
        # Load group configurations from somewhere?

        # Toon
        self.devices.append(ToonThermostatDevice(
            SecureSettings.get_string("eneco_username"),
            SecureSettings.get_string("eneco_pw"),
            SecureSettings.get_string("toon_consumer_id"),
            SecureSettings.get_string("toon_consumer_secret")))

        # Shelly's
        self.devices.append(ShellyLightDevice("fdsaf", "Shelly light", ""))

        # Tradfri (socket/lights)
        TradfriManager().init(self.light_device_change, self.switch_device_change)
        for device in TradfriManager().get_devices():
            self.devices.append(device)
        TradfriManager().start_observing()

        for device in self.devices:
            device.register_callback(lambda old, newv: self.changed())

        # Initialize all devices
        for device in self.devices:
            device.initialize()
        self.changed()

    def add_group(self, name):
        group = DeviceGroup(None, name)
        self.groups.append(group)
        self.changed()
        return group.id

    def set_group_name(self, id, name):
        group = [x for x in self.groups if x.id == id][0]
        group.name = name
        self.changed()

    def set_group_devices(self, id, device_ids):
        group = [x for x in self.groups if x.id == id][0]
        group.devices = [x for x in self.devices if x.id in device_ids]
        self.changed()

    def remove_group(self, id):
        group = [x for x in self.groups if x.id == id][0]
        self.groups.remove(group)
        self.changed()

    def get_device(self, device_id):
        return [x for x in self.devices if x.id == device_id][0]

    def get_group(self, group_id):
        return [x for x in self.groups if x.id == group_id][0]

    def light_device_change(self, id, state, dim, warmth):
        device = self.get_device(id)
        device.update(state, dim, warmth)

    def switch_device_change(self, id, state):
        device = self.get_device(id)
        device.update(state)

    def sensor_device_change(self, id, state):
        device = self.get_device(id)
        device.update(state)

    def thermostat_device_change(self, id, temperature, setpoint):
        device = self.get_device(id)
        device.update(temperature, setpoint)

    def register_device_callback(self, device_id, callback):
        device = self.get_device(device_id)
        device.register_callback(callback)


class DeviceGroup:

    def __init__(self, id, name):
        self.devices = []
        self.id = id
        self.state = False
        if id is None:
            self.id = random.randint(0, 999999999)
        self.name = name

    def add_device(self, device):
        self.devices.append(device)

    def remove_device(self, device):
        self.devices.remove(device)

    def set_state(self, state):
        for device in self.devices:
            if device.device_type == DeviceType.Light:
                device.set_on(state)
            elif device.device_type == DeviceType.Switch:
                device.set_active(state)
        self.state = state
