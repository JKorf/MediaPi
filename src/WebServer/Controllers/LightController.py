import sys
import traceback
import uuid

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import to_JSON


class LightController:

    api_factory = None
    api = None
    gateway = None
    enabled = False

    @staticmethod
    def init(program):
        if sys.platform != "linux" and sys.platform != "linux2":
            Logger.write(2, "Not initializing lighting, no coap client available on windows")
            return

        ip = "192.168.1.73"  # Hub ID
        identity = uuid.uuid4().hex
        key = program.database.get_stat("LightingId")
        if key == 0:
            key = None
            LightController.api_factory = APIFactory(host=ip, psk_id=identity)
        else:
            LightController.api_factory = APIFactory(host=ip, psk_id=identity, psk=key)

        LightController.api = LightController.api_factory.request
        LightController.gateway = Gateway()

        try:
            if key is None:
                Logger.write(2, "No key found for lighting, going to get new")
                # We don't have a key, generate a new one
                security_code = "zwhwlZr85gcfAtxr"  # the key at the bottom of the hub
                key = LightController.api_factory.generate_psk(security_code)
                program.database.update_stat("LightingId", key)
                Logger.write(2, "New key retrieved")

            LightController.enabled = True
        except Exception as e:
            stack_trace = traceback.format_exc().split('\n')
            for stack_line in stack_trace:
                Logger.write(3, stack_line)

    @staticmethod
    def get_lights():
        if not LightController.enabled:
            return to_JSON([])

        return to_JSON(LightController.get_devices())

    @staticmethod
    def debug():
        if not LightController.enabled:
            return

        gateway_info = LightController.api(LightController.gateway.get_gateway_info()).raw
        gateway_endpoints = LightController.api(LightController.gateway.get_endpoints())
        devices = LightController.get_devices()

        Logger.write(2, "Gateway info: " + to_JSON(gateway_info))
        Logger.write(2, "Gateway endpoints: " + to_JSON(gateway_endpoints))
        Logger.write(2, "Devices: " + to_JSON(devices))

    @staticmethod
    def switch_light(id, state):
        if not LightController.enabled:
            return

        devices = LightController.get_devices()
        light = [x for x in devices if x.id == id][0]
        light.light_control.set_state(state)

    @staticmethod
    def warmth_light(id, warmth):
        if not LightController.enabled:
            return

        devices = LightController.get_devices()
        light = [x for x in devices if x.id == id][0]
        light.light_control.set_color_temp(warmth)

    @staticmethod
    def dimmer_light(id, amount):
        if not LightController.enabled:
            return

        devices = LightController.get_devices()
        light = [x for x in devices if x.id == id][0]
        light.light_control.set_dimmer(amount)

    @staticmethod
    def get_devices():
        devices_commands = LightController.api(LightController.gateway.get_devices())
        return LightController.api(devices_commands)