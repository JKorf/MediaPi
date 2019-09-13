import random
import sys
import time
import uuid

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from Automation.DeviceBase import DeviceType
from Automation.Devices.TradfriLightDevice import TradfriLightDevice
from Automation.Devices.TradfriSocketDevice import TradfriSocketDevice
from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings, SecureSettings
from Shared.Threading import CustomThread
from Shared.Util import Singleton, current_time


class TradfriManager(metaclass=Singleton):
    def __init__(self):
        self.api_factory = None
        self.api = None
        self.gateway = None
        self.enabled = False
        self.initialized = False
        self.last_init = 0
        self.on_light_device_change = None
        self.on_socket_device_change = None

        self.observing = False
        self.observing_end = 0
        self.observe_thread = None

        self.test_devices = [
                TradfriLightDevice(None, None, "Light123", "Test light 1", True, False),
                TradfriLightDevice(None, None, "Light456", "Test light 2", True, False),
                TradfriLightDevice(None, None, "Light789", "Test light 3", True, False),
                TradfriLightDevice(None, None, "Light7891", "Test light 3", False, False),
                TradfriLightDevice(None, None, "Light7892", "Test light 4", False, False),
                TradfriLightDevice(None, None, "Light7893", "Test light 5", True, True),
                TradfriLightDevice(None, None, "Light7894", "Test light 6", True, True),
                TradfriLightDevice(None, None, "Light7895", "Test light 7", True, True),
                TradfriSocketDevice(None, None, "Socket123", "Test socket 1"),
                TradfriSocketDevice(None, None, "Socket456", "Test socket 2"),
            ]

    def init(self, on_light_device_change, on_socket_device_change):
        self.on_light_device_change = on_light_device_change
        self.on_socket_device_change = on_socket_device_change
        if self.initialized:
            return

        if sys.platform != "linux" and sys.platform != "linux2":
            Logger().write(LogVerbosity.Info, "Lighting: Not initializing, no coap client available on windows")
            self.initialized = True
            return

        if current_time() - self.last_init < 5000:
            Logger().write(LogVerbosity.Info, "Tried initialization less than 5s ago")
            return

        Logger().write(LogVerbosity.All, "Start LightManager init")
        self.enabled = True
        if not self.initialized:
            ip = Settings.get_string("tradfri_hub_ip")
            identity = Database().get_stat_string("LightingId")
            key = Database().get_stat_string("LightingKey")

            if identity is None or key is None:
                Logger().write(LogVerbosity.Info, "Lighting: No identity/key found, going to generate new")
                # We don't have all information to connect, reset and start from scratch
                Database().remove_stat("LightingId")
                Database().remove_stat("LightingKey")
                key = None

                identity = uuid.uuid4().hex
                Database().update_stat("LightingId", identity)  # Generate and save a new id
                self.api_factory = APIFactory(host=ip, psk_id=identity)
            else:
                self.api_factory = APIFactory(host=ip, psk_id=identity, psk=key)

            self.api = self.api_factory.request
            self.gateway = Gateway()

            if key is None:
                try:
                    security_code = SecureSettings.get_string("tradfri_hub_code")  # the code at the bottom of the hub
                    key = self.api_factory.generate_psk(security_code)
                    Database().update_stat("LightingKey", key)  # Save the new key
                    Logger().write(LogVerbosity.Info, "Lighting: New key retrieved")
                except Exception as e:
                    Logger().write_error(e, "Unhandled exception")
                    return
            else:
                Logger().write(LogVerbosity.Info, "Lighting: Previously saved key found")

            try:
                self.initialized = True
                self.api(self.api(self.gateway.get_groups()))  # check init was okay
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Failed to init tradfri, clearing previous key to try generate new")
                self.initialized = False
                Database().remove_stat("LightingId")
                Database().remove_stat("LightingKey")
                Logger().write_error(e, "Failed to get groups from hub")

    def get_devices(self):
        if sys.platform != "linux" and sys.platform != "linux2":
            return self.test_devices

        Logger().write(LogVerbosity.All, "Get devices")
        devices_commands = self.api(self.gateway.get_devices())
        devices = self.api(devices_commands)
        return [d for d in [self.parse_device(x) for x in devices] if d is not None]

    def parse_device(self, data):
        if data.has_light_control:
            return TradfriLightDevice(self.gateway, self.api, data.id, data.name, data.light_control.can_set_dimmer, data.light_control.can_set_temp)
        elif data.has_socket_control:
            return TradfriSocketDevice(self.gateway, self.api, data.id, data.name)

    def start_observing(self):
        Logger().write(LogVerbosity.Debug, "Start observing light data")

        if sys.platform != "linux" and sys.platform != "linux2":
            self.observe_thread = CustomThread(self.random_change, "Light device changer", [])
            self.observe_thread.start()
            return

        self.observing = True
        if self.observing_end > current_time():
            Logger().write(LogVerbosity.All, "Still observing, not starting again")
            return  # still observing, the check observing thread will renew

        self.observing_end = current_time() + 30000
        result = self.api(self.api(self.gateway.get_devices()))
        for device in result:
            self.observe_device(device)

    def observe_device(self, device):
        Logger().write(LogVerbosity.All, "Starting observe for device " + device.name)
        self.observe_thread = CustomThread(lambda: self.api(device.observe(
            self.device_change,
            lambda x: self.check_observe(device), duration=30)), "Light device observer", [])
        self.observe_thread.start()

    def device_change(self, device):
        if device.has_light_control:
            state = device.light_control.lights[0].state
            dim = device.light_control.lights[0].dimmer
            warmth = device.light_control.lights[0].warmth
            self.on_light_device_change(state, dim, warmth)
        else:
            state = device.socket_control.sockets[0].state
            self.on_socket_device_change(device.id, state)

    def check_observe(self, device):
        if self.observing:
            # Restart observing since it timed out
            Logger().write(LogVerbosity.Debug, "Restarting observing for group " + str(device.name))
            self.observe_device(device)

    def stop_observing(self):
        Logger().write(LogVerbosity.Debug, "Stop observing light data")
        self.observing = False

    def random_change(self):
        while True:
            device = random.choice(self.test_devices)
            state = bool(random.getrandbits(1))
            if device.device_type == DeviceType.Switch:
                self.on_socket_device_change(device.id, state)
            else:
                self.on_light_device_change(device.id, state, 0, 0)
            time.sleep(5)
