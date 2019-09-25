import random
import sys
import time
import uuid

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from Automation.DeviceBase import DeviceProvider
from Automation.Devices.TradfriLightDevice import TradfriLightDevice
from Automation.Devices.TradfriSocketDevice import TradfriSocketDevice
from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import current_time


class TradfriProvider(DeviceProvider):

    def __init__(self, name, ip, hub_code, testing, on_light_device_change, on_socket_device_change):
        super().__init__(name, ip, "TradfriHub")
        self.hub_code = hub_code
        self.testing = testing

        self.__api_factory = None
        self.__api = None
        self.__gateway = None
        self.__initialized = False
        self.__last_init = 0
        self.__on_light_device_change = on_light_device_change
        self.__on_socket_device_change = on_socket_device_change

        self.__observing = False
        self.__observing_end = 0
        self.__observe_thread = None

        self.__test_devices = [
                TradfriLightDevice(None, None, "Light123", "Test light 1", True, False, True),
                TradfriLightDevice(None, None, "Light456", "Test light 2", True, False, True),
                TradfriLightDevice(None, None, "Light789", "Test light 3", True, False, True),
                TradfriLightDevice(None, None, "Light7891", "Test light 3", True, False, False),
                TradfriLightDevice(None, None, "Light7892", "Test light 4", True, False, False),
                TradfriLightDevice(None, None, "Light7893", "Test light 5", True, True, True),
                TradfriLightDevice(None, None, "Light7894", "Test light 6", True, True, True),
                TradfriLightDevice(None, None, "Light7895", "Test light 7", True, True, True),
                TradfriSocketDevice(None, None, "Socket123", "Test socket 1", True),
                TradfriSocketDevice(None, None, "Socket456", "Test socket 2", True),
            ]

    def initialize(self):
        if self.__initialized:
            return True

        if sys.platform != "linux" and sys.platform != "linux2":
            Logger().write(LogVerbosity.Info, "Lighting: Not initializing, no coap client available on windows")
            self.__initialized = True
            return True

        Logger().write(LogVerbosity.All, "Start LightManager init")
        if not self.__initialized:
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
                self.__api_factory = APIFactory(host=self.ip, psk_id=identity)
            else:
                self.__api_factory = APIFactory(host=self.ip, psk_id=identity, psk=key)

            self.__api = self.__api_factory.request
            self.__gateway = Gateway()

            if key is None:
                try:
                    key = self.__api_factory.generate_psk(self.hub_code)  # bottom of hub code
                    Database().update_stat("LightingKey", key)  # Save the new key
                    Logger().write(LogVerbosity.Info, "Lighting: New key retrieved")
                except Exception as e:
                    Logger().write_error(e, "Unhandled exception")
                    return False
            else:
                Logger().write(LogVerbosity.Info, "Lighting: Previously saved key found")

            try:
                self.__initialized = True
                self.__api(self.__api(self.__gateway.get_groups()))  # check init was okay
                return True
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Failed to init tradfri, clearing previous key to try generate new")
                self.__initialized = False
                Database().remove_stat("LightingId")
                Database().remove_stat("LightingKey")
                Logger().write_error(e, "Failed to get groups from hub")
                return False

    def get_devices(self):
        if self.testing:
            return self.__test_devices

        Logger().write(LogVerbosity.All, "Get devices")
        devices_commands = self.__api(self.__gateway.get_devices())
        devices = self.__api(devices_commands)
        return [d for d in [self.parse_device(x) for x in devices] if d is not None]

    def parse_device(self, data):
        if data.has_light_control:
            return TradfriLightDevice(self.__gateway, self.__api, str(data.id), data.name, False, data.light_control.can_set_dimmer, data.light_control.can_set_temp)
        elif data.has_socket_control:
            return TradfriSocketDevice(self.__gateway, self.__api, str(data.id), data.name, False)
