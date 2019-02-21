import urllib.parse

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
        elif url == "get_group_lights":
            self.write(self.get_group_lights(int(self.get_argument("group"))))

    def post(self, url):
        if url == "set_light_state":
            self.set_light_state(int(self.get_argument("light")), self.get_argument("state") == "true")
        elif url == "set_light_warmth":
            self.set_light_warmth(int(self.get_argument("light")), int(self.get_argument("warmth")))
        elif url == "set_light_dimmer":
            self.set_light_dimmer(int(self.get_argument("light")), int(self.get_argument("dimmer")))
        elif url == "set_light_name":
            self.set_light_name(int(self.get_argument("light")), str(urllib.parse.unquote(self.get_argument("name"))))

        elif url == "set_group_state":
            self.set_group_state(int(self.get_argument("group")), self.get_argument("state") == "true")
        elif url == "set_group_dimmer":
            self.set_group_dimmer(int(self.get_argument("group")), int(self.get_argument("dimmer")))
        elif url == "set_group_name":
            self.set_group_name(int(self.get_argument("group")), str(urllib.parse.unquote(self.get_argument("name"))))

    def get_lights(self):
        devices = LightManager().get_lights()
        result = [self.parse_light_control(x) for x in devices if x.has_light_control]

        if len(result) == 0:
            result = self.create_test_data()

        return to_JSON(result)

    def set_light_name(self, light, name):
        Logger.write(2, "Set light " + str(light) + " to name " + str(name))
        LightManager().set_light_name(light, name)

    def set_light_state(self, light, state):
        Logger.write(2, "Set light " + str(light) + " to state " + str(state))
        LightManager().set_light_state(light, state)

    def set_light_warmth(self, light, warmth):
        Logger.write(2, "Set light " + str(light) + " to warmth " + str(warmth))
        LightManager().set_light_warmth(light, warmth)

    def set_light_dimmer(self, light, dimmer):
        Logger.write(2, "Set light " + str(light) + " to dimmer " + str(dimmer))
        LightManager().set_light_dimmer(light, dimmer)

    def get_groups(self):
        groups = LightManager().get_light_groups()
        result = [LightGroup(group.id, group.name, group.state, group.dimmer) for group in groups]

        if len(result) == 0:
            result = self.create_test_groups()
        return to_JSON(result)

    def get_group_lights(self, group):
        lights = LightManager().get_lights_in_group(group)
        result = [self.parse_light_control(x) for x in lights if x.has_light_control]

        if len(result) == 0:
            result = self.create_test_data()

        return to_JSON(result)

    def set_group_state(self, group, state):
        Logger.write(2, "Set group " + str(group) + " to state " + str(state))
        LightManager().set_group_state(group, state)

    def set_group_dimmer(self, group, dimmer):
        Logger.write(2, "Set group " + str(group) + " to dimmer " + str(dimmer))
        LightManager().set_group_dimmer(group, dimmer)

    def set_group_name(self, group, name):
        Logger.write(2, "Set group " + str(group) + " to name " + str(name))
        LightManager().set_group_name(group, name)

    def parse_light_control(self, data):
        lights = []
        for light in data.light_control.lights:
            lights.append(LightDevice(
                light.state,
                light.dimmer,
                light.color_temp,
                light.hex_color))

        return LightControl(data.id,
                            data.name,
                            data.application_type,
                            data.last_seen.timestamp(),
                            data.reachable,
                            data.light_control.can_set_dimmer,
                            data.light_control.can_set_temp,
                            data.light_control.can_set_color,
                            lights)

    def create_test_groups(self):
        return [LightGroup(1, "Woonkamer 1", True, 254), LightGroup(2, "Woonkamer 2", True, 128), LightGroup(3, "Keuken", False, 254)]

    def create_test_data(self):
        result = []

        result.append(LightControl(1,
                     "Test led",
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
                                   "Test led 2",
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

        result.append(LightControl(2,
                                   "Test led 3",
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

        result.append(LightControl(2,
                                   "Test led 4",
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

        result.append(LightControl(2,
                                   "Test led 5",
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
