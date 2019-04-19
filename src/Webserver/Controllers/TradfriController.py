import urllib.parse

from flask import request

from Controllers.TradfriManager import TradfriManager
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import to_JSON
from Webserver.APIController import app
from Webserver.Models import LightControl, LightDevice, DeviceGroup, SocketControl, SocketDevice


class TradfriController:
    @staticmethod
    @app.route('/tradfri/devices', methods=['GET'])
    def get_devices():
        result = TradfriManager().get_devices()

        if len(result) == 0:
            result = TradfriController.create_test_data()

        return to_JSON(result)

    @staticmethod
    @app.route('/tradfri/device_name', methods=['POST'])
    def set_device_name():
        device_id = int(request.args.get('device_id'))
        name = urllib.parse.unquote(request.args.get('name'))

        Logger().write(LogVerbosity.Info, "Set device " + str(device_id) + " to name " + str(name))
        TradfriManager().set_device_name(device_id, name)
        return "OK"

    @staticmethod
    @app.route('/tradfri/device_state', methods=['POST'])
    def set_device_state():
        device_id = int(request.args.get('device_id'))
        state = request.args.get('state') == "true"

        Logger().write(LogVerbosity.Info, "Set device " + str(device_id) + " to state " + str(state))
        TradfriManager().set_state(device_id, state)
        return "OK"

    @staticmethod
    @app.route('/tradfri/light_warmth', methods=['POST'])
    def set_light_warmth():
        device_id = int(request.args.get('device_id'))
        warmth = int(request.args.get('warmth'))

        Logger().write(LogVerbosity.Info, "Set light " + str(device_id) + " to warmth " + str(warmth))
        TradfriManager().set_light_warmth(device_id, warmth)
        return "OK"

    @staticmethod
    @app.route('/tradfri/light_dimmer', methods=['POST'])
    def set_light_dimmer():
        device_id = int(request.args.get('device_id'))
        dimmer = int(request.args.get('dimmer'))

        Logger().write(LogVerbosity.Info, "Set light " + str(device_id) + " to dimmer " + str(dimmer))
        TradfriManager().set_light_dimmer(device_id, dimmer)
        return "OK"

    @staticmethod
    @app.route('/tradfri/groups', methods=['GET'])
    def get_groups():
        result = TradfriManager().get_device_groups()
        if len(result) == 0:
            result = TradfriController.create_test_groups()
        return to_JSON(result)

    @staticmethod
    @app.route('/tradfri/group_devices', methods=['GET'])
    def get_group_devices():
        group_id = int(request.args.get('group_id'))

        result = TradfriManager().get_devices_in_group(group_id)

        if len(result) == 0:
            result = TradfriController.create_test_data()

        return to_JSON(result)

    @staticmethod
    @app.route('/tradfri/group_state', methods=['POST'])
    def set_group_state():
        group_id = int(request.args.get('group_id'))
        state = request.args.get('state') == "true"

        Logger().write(LogVerbosity.Info, "Set group " + str(group_id) + " to state " + str(state))
        TradfriManager().set_group_state(group_id, state)
        return "OK"

    @staticmethod
    @app.route('/tradfri/group_dimmer', methods=['POST'])
    def set_group_dimmer():
        group_id = int(request.args.get('group_id'))
        dimmer = int(request.args.get('dimmer'))

        Logger().write(LogVerbosity.Info, "Set group " + str(group_id) + " to dimmer " + str(dimmer))
        TradfriManager().set_group_dimmer(group_id, dimmer)
        return "OK"

    @staticmethod
    @app.route('/tradfri/group_name', methods=['POST'])
    def set_group_name():
        group_id = int(request.args.get('group_id'))
        name = urllib.parse.unquote(request.args.get('name'))

        Logger().write(LogVerbosity.Info, "Set group " + str(group_id) + " to name " + str(name))
        TradfriManager().set_group_name(group_id, name)
        return "OK"

    @staticmethod
    def create_test_groups():
        return [DeviceGroup(1, "Woonkamer 1", True, 254, 6), DeviceGroup(2, "Woonkamer 2", True, 128, 6), DeviceGroup(3, "Keuken", False, 254, 6)]

    @staticmethod
    def create_test_data():
        result = [LightControl(1,
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
                               ]), SocketControl(2,
                                                "Test socket 2",
                                                "Type",
                                                123,
                                                True,
                                                [
                                                    SocketDevice(False)
                                                ]), LightControl(3,
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
                                                                 ]), LightControl(4,
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
                                                                                  ]), LightControl(5,
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
                                                                                                   ])]

        return result
