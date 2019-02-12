from Controllers.LightManager import LightManager
from Shared.Util import to_JSON
from Webserver.BaseHandler import BaseHandler
from Webserver.Models import LightControl, LightDevice


class LightController(BaseHandler):
    def get(self, url):
        if url == "get_lights":
            self.write(self.get_lights())

    def post(self, url):
        if url == "switch_light":
            self.switch_light(int(self.get_argument("index")), self.get_argument("state") == "on")
        elif url == "warmth_light":
            self.warmth_light(int(self.get_argument("index")), int(self.get_argument("warmth")))
        elif url == "dimmer_light":
            self.dimmer_light(int(self.get_argument("index")), int(self.get_argument("dimmer")))

    def get_lights(self):
        devices = LightManager().get_lights()
        result = []
        i = 0
        for control_device in [x for x in devices if x.has_light_control]:
            lights = []
            for light in control_device.light_control.lights:
                lights.append(LightDevice(
                    light.state,
                    light.dimmer,
                    light.color_temp,
                    light.hex_color))

            result.append(LightControl(i,
                                       control_device.application_type,
                                       control_device.last_seen.timestamp(),
                                       control_device.reachable,
                                       control_device.light_control.can_set_dimmer,
                                       control_device.light_control.can_set_temp,
                                       control_device.light_control.can_set_color,
                                       lights))
            i += 1

        return to_JSON(result)

    def switch_light(self, index, state):
        LightManager().switch_light(index, state)

    def warmth_light(self, index, warmth):
        LightManager().warmth_light(index, warmth)

    def dimmer_light(self, index, amount):
        LightManager().dimmer_light(index, amount)
