import json
import os
import random

from Automation.DeviceBase import DeviceType
from Automation.Devices.ShellyLightDevice import ShellyLightDevice
from Automation.Devices.ToonThermostatDevice import ToonThermostatDevice
from Automation.Providers.TradfriProvider import TradfriProvider
from Shared.Logger import LogVerbosity, Logger
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import Singleton, to_JSON


class DeviceController(Observable, metaclass=Singleton):

    def __init__(self):
        super().__init__("DeviceData", 0.5)

        self.providers = []
        self.devices = []
        self.groups = []

    def initialize(self):
        self.load_configuration()
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
        self.save_configuration()

    def set_group_devices(self, id, device_ids):
        group = [x for x in self.groups if x.id == id][0]
        group.devices = [x for x in self.devices if x.id in device_ids]
        self.changed()
        self.save_configuration()

    def remove_group(self, id):
        group = [x for x in self.groups if x.id == id][0]
        self.groups.remove(group)
        self.changed()
        self.save_configuration()

    def set_device_name(self, device_id, name):
        device = self.get_device(device_id)
        device.set_name(name)
        self.save_configuration()

    def get_device(self, device_id):
        return [x for x in self.devices if x.id == device_id][0]

    def get_devices_by_type(self, device_type):
        return [x for x in self.devices if x.device_type == device_type]

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
        return device.register_callback(callback)

    def unregister_device_callback(self, device_id, registration_id):
        device = self.get_device(device_id)
        device.remove_callback(registration_id)

    def load_configuration(self):
        path = Settings.get_string("base_folder") + 'Solution/device_configuration.txt'
        if not os.path.exists(path):
            Logger().write(LogVerbosity.Info, "No device configuration found at " + Settings.get_string("base_folder") + 'Solution/device_configuration.txt')

            # self.devices.append(ShellyLightDevice("Shelly1", "Shelly light 1", "192.168.2.120", True))
            # self.devices.append(ShellyLightDevice("Shelly2", "Shelly light 2", "192.168.2.121", True))
            # self.devices.append(ToonThermostatDevice(True, "USER", "PW", "CONS_ID", "CONS_SEC"))
            #
            # self.providers.append(TradfriProvider("Hub1", "192.168.2.73", "XXX", True, self.light_device_change, self.switch_device_change))
            # self.save_configuration()
            return

        Logger().write(LogVerbosity.Info, "Reading device configuration")
        with open(path) as file:
            data = json.loads(file.read())
            for provider in data['providers']:
                if provider['type'] == 'TradfriHub':
                    self.providers.append(
                        TradfriProvider(
                            provider['name'],
                            provider['ip'],
                            provider['hub_code'],
                            provider['testing'],
                            self.light_device_change,
                            self.switch_device_change))
                    Logger().write(LogVerbosity.Debug, "Added Tradfri provider")

            threads = []
            for provider in self.providers:
                thread = CustomThread(self.init_provider, provider.type + " init", [provider])
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            for device in data['devices']:
                if device['implementation_type'] == 'ShellyLight':
                    self.devices.append(
                        ShellyLightDevice(
                            device['id'],
                            device['name'],
                            device['ip_address'],
                            device['testing']))
                    Logger().write(LogVerbosity.Debug, "Added ShellyLight device")

                if device['implementation_type'] == 'ToonThermostat':
                    self.devices.append(
                        ToonThermostatDevice(
                            device['testing'],
                            device['eneco_username'],
                            device['eneco_password'],
                            device['eneco_consumer_id'],
                            device['eneco_consumer_secret']))
                    Logger().write(LogVerbosity.Debug, "Added ToonThermostat device")

            threads = []
            for device in self.devices:  # is it okay to call tradfri hub concurrently?
                thread = CustomThread(self.init_device, device.name + " init", [device])
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            for group in data['groups']:
                g = DeviceGroup(int(group['id']), group['name'])
                g.devices = [x for x in self.devices if x.id in group['devices']]
                self.groups.append(g)

    def init_provider(self, provider):
        provider.accessible = provider.initialize()
        if provider.accessible:
            self.devices += provider.get_devices()
        Logger().write(LogVerbosity.Debug, provider.type + " init done. Accessible: " + str(provider.accessible))

    def init_device(self, device):
        device.register_callback(lambda old, newv: self.changed())
        device.accessible = device.initialize()
        Logger().write(LogVerbosity.Debug, device.name + " init done. Accessible: " + str(device.accessible))

    def save_configuration(self):
        with open(Settings.get_string("base_folder") + 'Solution/device_configuration.txt', 'w+') as file:
            file.write(to_JSON(Configuration(self.devices, self.groups, self.providers)))


class DeviceGroup:

    def __init__(self, id, name):
        self.devices = []
        self.id = id
        self.state = False
        self.dim = 100

        if id is None:
            self.id = random.randint(0, 999999999)
        self.name = name

    def add_device(self, device):
        self.devices.append(device)

    def remove_device(self, device):
        self.devices.remove(device)

    def set_state(self, state, src):
        for device in self.devices:
            if device.device_type == DeviceType.Light:
                device.set_on(state, src)
            elif device.device_type == DeviceType.Switch:
                device.set_active(state, src)
        self.state = state

    def set_dim(self, dim, src):
        for device in self.devices:
            if device.device_type == DeviceType.Light and device.can_dim:
                device.set_dim(dim, src)
        self.dim = dim


class Configuration:

    def __init__(self, devices, groups, providers):
        self.devices = [x for x in devices if x.is_base_device]
        self.providers = providers
        self.groups = [ConfigurationGroup(x) for x in groups]


class ConfigurationGroup:

    def __init__(self, group):
        self.id = group.id
        self.name = group.name
        self.devices = [x.id for x in group.devices]