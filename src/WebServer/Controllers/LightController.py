import sys
import traceback
import uuid
from threading import Lock

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory
from pytradfri.const import SUPPORT_BRIGHTNESS, SUPPORT_COLOR_TEMP, SUPPORT_HEX_COLOR

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import to_JSON
from WebServer.Models import LightControl, LightDevice


class LightController:

    program = None
    api_factory = None
    api = None
    gateway = None
    enabled = False
    devices = []
    initialized = False
    init_lock = Lock()

    @staticmethod
    def init():
        if LightController.initialized:
            return

        with LightController.init_lock:
            if sys.platform != "linux" and sys.platform != "linux2":
                Logger.write(2, "Lighting: Not initializing, no coap client available on windows")
                LightController.initialized = True
                return

            LightController.enabled = True
            if not LightController.initialized:
                ip = Settings.get_string("tradfri_hub_ip")
                identity = LightController.program.database.get_stat_string("LightingId")
                key = LightController.program.database.get_stat_string("LightingKey")

                if identity is None or key is None:
                    key = None
                    Logger.write(2, "Lighting: No identity/key found, going to generate new")
                    identity = uuid.uuid4().hex
                    LightController.program.database.update_stat("LightingId", identity)  # Generate and save a new id
                    LightController.api_factory = APIFactory(host=ip, psk_id=identity)
                else:
                    LightController.api_factory = APIFactory(host=ip, psk_id=identity, psk=key)

                LightController.api = LightController.api_factory.request
                LightController.gateway = Gateway()

                if key is None:
                    try:
                        security_code = Settings.get_string("tradfri_hub_code")  # the code at the bottom of the hub
                        key = LightController.api_factory.generate_psk(security_code)
                        LightController.program.database.update_stat("LightingKey", key)  # Save the new key
                        Logger.write(2, "Lighting: New key retrieved")
                        LightController.initialized = True
                    except Exception as e:
                        stack_trace = traceback.format_exc().split('\n')
                        for stack_line in stack_trace:
                            Logger.write(3, stack_line)
                else:
                    Logger.write(2, "Lighting: Previously saved key found")
                    LightController.initialized = True


    @staticmethod
    def get_lights():
        if not LightController.check_state():
            return to_JSON([])

        LightController.get_devices()

        result = []
        i = 0
        for control_device in [x for x in LightController.devices if x.has_light_control]:
            lights = []
            for light in control_device.light_control.lights:
                lights.append(LightDevice(
                    light.supported_features & SUPPORT_BRIGHTNESS,
                    light.supported_features & SUPPORT_COLOR_TEMP,
                    light.supported_features & SUPPORT_HEX_COLOR,
                    light.state,
                    light.dimmer,
                    light.color_temp,
                    light.hex_color))

            result.append(LightControl(i, control_device.application_type, control_device.last_seen.timestamp(), control_device.reachable, lights))
            i += 1

        return to_JSON(result)

    @staticmethod
    def debug():
        if not LightController.check_state():
            return

        gateway_info = LightController.api(LightController.gateway.get_gateway_info()).raw
        gateway_endpoints = LightController.api(LightController.gateway.get_endpoints())
        LightController.get_devices()

        Logger.write(2, "Gateway info: " + to_JSON(gateway_info))
        Logger.write(2, "Gateway endpoints: " + to_JSON(gateway_endpoints))
        Logger.write(2, "Devices: " + to_JSON(LightController.devices))

    @staticmethod
    def switch_light(index, state):
        if not LightController.check_state():
            return

        light = LightController.devices[index]
        light.light_control.set_state(state)

    @staticmethod
    def warmth_light(index, warmth):
        if not LightController.check_state():
            return

        light = LightController.devices[index]
        light.light_control.set_color_temp(warmth)

    @staticmethod
    def dimmer_light(index, amount):
        if not LightController.check_state():
            return

        light = LightController.devices[index]
        light.light_control.set_dimmer(amount)

    @staticmethod
    def get_devices():
        devices_commands = LightController.api(LightController.gateway.get_devices())
        LightController.devices = LightController.api(devices_commands)

    @staticmethod
    def check_state():
        if not LightController.enabled:
            return False  # not available

        if not LightController.initialized:
            LightController.init()
            if not LightController.initialized:
                return False  # init failed
        return True
