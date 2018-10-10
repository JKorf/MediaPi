from pytradfri.const import SUPPORT_BRIGHTNESS, SUPPORT_COLOR_TEMP, SUPPORT_HEX_COLOR

from Automation.LightManager import LightManager
from Shared.Util import to_JSON
from WebServer.Models import LightControl, LightDevice


class LightController:

    @staticmethod
    def get_lights():
        devices = LightManager().get_lights()
        result = []
        i = 0
        for control_device in [x for x in devices if x.has_light_control]:
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
    def switch_light(index, state):
        LightManager().switch_light(index, state)

    @staticmethod
    def warmth_light(index, warmth):
        LightManager().warmth_light(index, warmth)

    @staticmethod
    def dimmer_light(index, amount):
        LightManager().dimmer_light(index, amount)
