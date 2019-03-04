import sys
import traceback
import uuid
from threading import Lock

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from Database.Database import Database
from Shared.Logger import Logger
from Shared.Settings import Settings, SecureSettings
from Shared.Util import Singleton


class LightManager(metaclass=Singleton):

    api_factory = None
    api = None
    gateway = None
    enabled = False
    initialized = False
    init_lock = Lock()

    def init(self):
        if self.initialized:
            Logger().write(2, "already init")
            return

        with self.init_lock:
            if sys.platform != "linux" and sys.platform != "linux2":
                Logger().write(2, "Lighting: Not initializing, no coap client available on windows")
                self.initialized = True
                return

            self.enabled = True
            if not self.initialized:
                ip = Settings.get_string("tradfri_hub_ip")
                identity = Database().get_stat_string("LightingId")
                key = Database().get_stat_string("LightingKey")

                if identity is None or key is None:
                    Logger().write(2, "Lighting: No identity/key found, going to generate new")
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
                        Logger().write(2, "Lighting: New key retrieved")
                        self.initialized = True
                    except Exception:
                        stack_trace = traceback.format_exc().split('\n')
                        for stack_line in stack_trace:
                            Logger().write(3, stack_line)
                else:
                    Logger().write(2, "Lighting: Previously saved key found")
                    self.initialized = True

    def get_lights(self):
        if not self.check_state():
            return []

        devices_commands = self.api(self.gateway.get_devices())
        return self.api(devices_commands)

    def set_light_state(self, light, state):
        if not self.check_state():
            return

        device = self.api(self.gateway.get_device(light))
        self.api(device.light_control.set_state(state))

    def set_light_warmth(self, light, warmth):
        if not self.check_state():
            return

        device = self.api(self.gateway.get_device(light))
        self.api(device.light_control.set_color_temp(warmth))

    def set_light_dimmer(self, light, amount):
        if not self.check_state():
            return

        device = self.api(self.gateway.get_device(light))
        self.api(device.light_control.set_dimmer(amount))

    def set_light_name(self, light, name):
        if not self.check_state():
            return

        device = self.api(self.gateway.get_device(light))
        self.api(device.set_name(name))

    def get_light_groups(self):
        if not self.check_state():
            return []

        groups_commands = self.api(self.gateway.get_groups())
        result = self.api(groups_commands)
        Logger().write(2, "Get light groups 1: " + str(result))
        Logger().write(2, "Get light groups 2: " + str([x.raw for x in result]))
        return result

    def get_lights_in_group(self, group):
        if not self.check_state():
            return []

        group = self.api(self.gateway.get_group(group))
        members = group.member_ids
        return [self.api(self.gateway.get_device(x)) for x in members]

    def set_group_name(self, group, name):
        if not self.check_state():
            return

        group = self.api(self.gateway.get_group(group))
        self.api(group.set_name(name))

    def set_group_state(self, group, state):
        if not self.check_state():
            return

        group = self.api(self.gateway.get_group(group))
        self.api(group.set_state(state))

    def set_group_dimmer(self, group, dimmer):
        if not self.check_state():
            return

        group = self.api(self.gateway.get_group(group))
        self.api(group.set_dimmer(dimmer))

    def check_state(self):
        if not self.enabled:
            return False  # not available

        if not self.initialized:
            self.init()
            if not self.initialized:
                return False  # init failed
        return True

