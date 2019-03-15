import urllib.parse

from flask import request

from Controllers.LightManager import LightManager
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.APIController import app
from Webserver.Models import LightControl, LightDevice, LightGroup


class LightController:

    @staticmethod
    @app.route('/lighting/lights', methods=['GET'])
    def get_lights():
        result = LightManager().get_lights()

        if len(result) == 0:
            result = LightController.create_test_data()

        return to_JSON(result)

    @staticmethod
    @app.route('/lighting/light_name', methods=['POST'])
    def set_light_name():
        light = int(request.args.get('light'))
        name = urllib.parse.unquote(request.args.get('name'))

        Logger().write(LogVerbosity.Info, "Set light " + str(light) + " to name " + str(name))
        LightManager().set_light_name(light, name)
        return "OK"

    @staticmethod
    @app.route('/lighting/light_state', methods=['POST'])
    def set_light_state():
        light = int(request.args.get('light'))
        state = request.args.get('state') == "true"

        Logger().write(LogVerbosity.Info, "Set light " + str(light) + " to state " + str(state))
        LightManager().set_light_state(light, state)
        return "OK"

    @staticmethod
    @app.route('/lighting/light_warmth', methods=['POST'])
    def set_light_warmth():
        light = int(request.args.get('light'))
        warmth = int(request.args.get('warmth'))

        Logger().write(LogVerbosity.Info, "Set light " + str(light) + " to warmth " + str(warmth))
        LightManager().set_light_warmth(light, warmth)
        return "OK"

    @staticmethod
    @app.route('/lighting/light_dimmer', methods=['POST'])
    def set_light_dimmer():
        light = int(request.args.get('light'))
        dimmer = int(request.args.get('dimmer'))

        Logger().write(LogVerbosity.Info, "Set light " + str(light) + " to dimmer " + str(dimmer))
        LightManager().set_light_dimmer(light, dimmer)
        return "OK"

    @staticmethod
    @app.route('/lighting/groups', methods=['GET'])
    def get_groups():
        result = LightManager().get_light_groups()
        if len(result) == 0:
            result = LightController.create_test_groups()
        return to_JSON(result)

    @staticmethod
    @app.route('/lighting/group_lights', methods=['GET'])
    def get_group_lights():
        group = int(request.args.get('group'))

        result = LightManager().get_lights_in_group(group)

        if len(result) == 0:
            result = LightController.create_test_data()

        return to_JSON(result)

    @staticmethod
    @app.route('/lighting/group_state', methods=['POST'])
    def set_group_state():
        group = int(request.args.get('group'))
        state = request.args.get('state') == "true"

        Logger().write(LogVerbosity.Info, "Set group " + str(group) + " to state " + str(state))
        LightManager().set_group_state(group, state)
        return "OK"

    @staticmethod
    @app.route('/lighting/group_dimmer', methods=['POST'])
    def set_group_dimmer():
        group = int(request.args.get('group'))
        dimmer = int(request.args.get('dimmer'))

        Logger().write(LogVerbosity.Info, "Set group " + str(group) + " to dimmer " + str(dimmer))
        LightManager().set_group_dimmer(group, dimmer)
        return "OK"

    @staticmethod
    @app.route('/lighting/group_name', methods=['POST'])
    def set_group_name():
        group = int(request.args.get('group'))
        name = urllib.parse.unquote(request.args.get('name'))

        Logger().write(LogVerbosity.Info, "Set group " + str(group) + " to name " + str(name))
        LightManager().set_group_name(group, name)
        return "OK"

    @staticmethod
    def create_test_groups():
        return [LightGroup(1, "Woonkamer 1", True, 254), LightGroup(2, "Woonkamer 2", True, 128), LightGroup(3, "Keuken", False, 254)]

    @staticmethod
    def create_test_data():
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

        result.append(LightControl(3,
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

        result.append(LightControl(4,
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

        result.append(LightControl(5,
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
