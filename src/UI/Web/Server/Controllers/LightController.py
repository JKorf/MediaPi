from Controllers.LightController import LightManager
from Shared.Util import to_JSON
from UI.Web.Server.Models import LightControl, LightDevice


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
                    control_device.light_control.can_set_dimmer,
                    control_device.light_control.can_set_temp,
                    control_device.light_control.can_set_color,
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
