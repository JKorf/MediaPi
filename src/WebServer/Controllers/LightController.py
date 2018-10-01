import sys
from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import to_JSON


class LightController:

    api_factory = None
    api = None
    gateway = None
    devices = []
    enabled = False

    @staticmethod
    def init(program):
        if sys.platform == "linux" or sys.platform == "linux2":
            ip = "192.168.1.0"  # Hub ID
            identity = Settings.get_string("name")
            key = program.database.get_stat("LightingId")
            if key == 0:
                key = None

            LightController.api_factory = APIFactory(host=ip, psk_id=identity, psk=key)
            LightController.api = LightController.api_factory.request
            LightController.gateway = Gateway()

            try:
                if key is None:
                    # We don't have a key, generate a new one
                    key = ""  # the key at the bottom of the hub
                    key = LightController.api_factory.generate_psk(key)
                    program.database.update_stat("LightingId", key)

                devices_command = LightController.gateway.get_devices()
                devices_commands = LightController.api(devices_command)
                LightController.devices = LightController.api(devices_commands)
                LightController.enabled = True
            except Exception as e:
                Logger.write(2, "Failed to initialize lighting: " + str(e), "error")
        else:
            Logger.write(2, "Not initializing lighting, no coap client available on windows")

    @staticmethod
    def get_lights():
        return to_JSON(LightController.devices)

    @staticmethod
    def switch_light(id, state):
        light = [x for x in LightController.devices if x.id == id][0]
        light.light_control.lights[0].set_state(state)

    @staticmethod
    def dim_light(id, amount):
        pass

    @staticmethod
    def change_warmth_light(id, amount):
        pass
