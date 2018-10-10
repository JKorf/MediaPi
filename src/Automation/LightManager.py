import sys
import traceback
import uuid
from threading import Lock

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from Database.Database import Database
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import Singleton


class LightManager(metaclass=Singleton):

    api_factory = None
    api = None
    gateway = None
    enabled = False
    devices = []
    initialized = False
    init_lock = Lock()

    def init(self):
        if self.initialized:
            Logger.write(2, "already init")
            return

        with self.init_lock:
            if sys.platform != "linux" and sys.platform != "linux2":
                Logger.write(2, "Lighting: Not initializing, no coap client available on windows")
                self.initialized = True
                return

            self.enabled = True
            if not self.initialized:
                ip = Settings.get_string("tradfri_hub_ip")
                identity = Database().get_stat_string("LightingId")
                key = Database().get_stat_string("LightingKey")

                if identity is None or key is None:
                    key = None
                    Logger.write(2, "Lighting: No identity/key found, going to generate new")
                    identity = uuid.uuid4().hex
                    Database().update_stat("LightingId", identity)  # Generate and save a new id
                    self.api_factory = APIFactory(host=ip, psk_id=identity)
                else:
                    self.api_factory = APIFactory(host=ip, psk_id=identity, psk=key)

                self.api = self.api_factory.request
                self.gateway = Gateway()

                if key is None:
                    try:
                        security_code = Settings.get_string("tradfri_hub_code")  # the code at the bottom of the hub
                        key = self.api_factory.generate_psk(security_code)
                        Database().update_stat("LightingKey", key)  # Save the new key
                        Logger.write(2, "Lighting: New key retrieved")
                        self.initialized = True
                    except Exception as e:
                        stack_trace = traceback.format_exc().split('\n')
                        for stack_line in stack_trace:
                            Logger.write(3, stack_line)
                else:
                    Logger.write(2, "Lighting: Previously saved key found")
                    self.initialized = True

    def get_lights(self):
        if not self.check_state():
            return []

        devices_commands = self.api(self.gateway.get_devices())
        return self.api(devices_commands)

    def switch_light(self, index, state):
        if not self.check_state():
            return

        light = self.get_device_by_index(index)
        light.light_control.set_state(state)

    def warmth_light(self, index, warmth):
        if not self.check_state():
            return

        light = self.get_device_by_index(index)
        light.light_control.set_color_temp(warmth)

    def dimmer_light(self, index, amount):
        if not self.check_state():
            return

        light = self.get_device_by_index(index)
        light.light_control.set_dimmer(amount)

    def get_device_by_index(self, index):
        i = 0
        for control_device in [x for x in self.devices if x.has_light_control]:
            if i == index:
                return control_device
            i += 1
        return None

    def check_state(self):
        if not self.enabled:
            return False  # not available

        if not self.initialized:
            self.init()
            if not self.initialized:
                return False  # init failed
        return True

