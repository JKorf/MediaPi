from Controllers.LightManager import LightManager
from Shared.Logger import Logger
from Shared.Util import to_JSON
from Webserver.BaseHandler import BaseHandler
from Webserver.Models import LightControl, LightDevice, LightGroup


class LightController(BaseHandler):
    def get(self, url):
        if url == "get_lights":
            self.write(self.get_lights())
        elif url == "get_groups":
            self.write(self.get_groups())

    def post(self, url):
        if url == "switch_light":
            self.switch_light(int(self.get_argument("index")), self.get_argument("state") == "on")
        elif url == "warmth_light":
            self.warmth_light(int(self.get_argument("index")), int(self.get_argument("warmth")))
        elif url == "dimmer_light":
            self.dimmer_light(int(self.get_argument("index")), int(self.get_argument("dimmer")))

        elif url == "set_group_state":
            self.set_group_state(int(self.get_argument("group")), self.get_argument("state") == "true")
        elif url == "set_group_dimmer":
            self.set_group_dimmer(int(self.get_argument("group")), int(self.get_argument("dimmer")))

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

        if len(result) == 0:
            result = self.create_test_data()

        return to_JSON(result)

    def get_groups(self):
        groups = LightManager().get_light_groups()
        result = [LightGroup(group.id, group.name, group.state, group.dimmer) for group in groups]

        if len(result) == 0:
            result = self.create_test_groups()
        return to_JSON(result)

    def switch_light(self, index, state):
        LightManager().switch_light(index, state)

    def warmth_light(self, index, warmth):
        LightManager().warmth_light(index, warmth)

    def dimmer_light(self, index, amount):
        LightManager().dimmer_light(index, amount)

    def set_group_state(self, group, state):
        Logger.write(2, "Set " + str(group) + " to " + str(state))
        LightManager().switch_group(group, state)

    def set_group_dimmer(self, group, dimmer):
        Logger.write(2, "Set " + str(group) + " to " + str(dimmer))
        LightManager().switch_group(group, dimmer)

    def create_test_groups(self):
        return [LightGroup(1, "Woonkamer 1", True, 254), LightGroup(2, "Woonkamer 2", True, 128), LightGroup(3, "Keuken", False, 254)]

    def create_test_data(self):
        result = []

        result.append(LightControl(1,
                     "Type",
                     123,
                     True,
                     True,
                     True,
                     True,
                     [
                         LightDevice(
                             True,
                             200,
                             260,
                             "4a418a")
                     ]))

        result.append(LightControl(2,
                                   "Type",
                                   123,
                                   True,
                                   True,
                                   False,
                                   False,
                                   [
                                       LightDevice(
                                           False,
                                           200,
                                           0,
                                           "")
                                   ]))

        return result
