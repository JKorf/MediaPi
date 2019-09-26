from flask import request
import urllib.parse

from Automation.DeviceBase import DeviceType
from Automation.DeviceController import DeviceController
from Controllers.RuleManager import RuleManager
from Database.Database import Database
from Shared.Logger import LogVerbosity, Logger
from Shared.Util import to_JSON, current_time
from Webserver.APIController import app


class HomeController:

    @staticmethod
    @app.route('/home/get_overview', methods=['GET'])
    def home_get_overview():
        return to_JSON([DeviceController().groups, DeviceController().devices])

    @staticmethod
    @app.route('/home/get_devices', methods=['GET'])
    def home_get_devices():
        return to_JSON(DeviceController().devices)

    @staticmethod
    @app.route('/home/get_groups', methods=['GET'])
    def home_get_groups():
        return to_JSON(DeviceController().groups)

    @staticmethod
    @app.route('/home/get_group', methods=['GET'])
    def home_get_group():
        id = int(request.args.get('id'))
        return to_JSON([x for x in DeviceController().groups if x.id == id][0])

    @staticmethod
    @app.route('/home/save_group', methods=['POST'])
    def home_save_group():
        id = int(request.args.get('id'))
        name = request.args.get('name')
        devices = request.args.get('devices')
        device_ids = [x for x in devices.split(',') if x is not '']
        if id == -1:
            group_id = DeviceController().add_group(name)
            DeviceController().set_group_devices(group_id, device_ids)
        else:
            DeviceController().set_group_name(id, name)
            DeviceController().set_group_devices(id, device_ids)

        return "OK"

    @staticmethod
    @app.route('/home/remove_group', methods=['POST'])
    def home_remove_group():
        id = int(request.args.get('id'))
        DeviceController().remove_group(id)
        RuleManager().device_group_removed(id)
        return "OK"

    @staticmethod
    @app.route('/home/set_device_name', methods=['POST'])
    def home_set_name():
        device_id = request.args.get('device_id')
        name = urllib.parse.unquote(request.args.get('name'))
        DeviceController().set_device_name(device_id, name)
        return "OK"

    @staticmethod
    @app.route('/home/set_setpoint', methods=['POST'])
    def home_set_temperature():
        device_id = request.args.get('device_id')
        temp = float(request.args.get('temperature'))
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Thermostat:
            raise TypeError("Can't set temperature on device of type " + str(device.device_type))

        device.set_setpoint(temp, "user")
        return "OK"

    @staticmethod
    @app.route('/home/set_light_state', methods=['POST'])
    def home_set_light_state():
        device_id = request.args.get('device_id')
        on = request.args.get('state') == "true"
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Light:
            raise TypeError("Can't set light on device of type " + str(device.device_type))
        device.set_on(on, "user")
        return "OK"

    @staticmethod
    @app.route('/home/set_light_dimmer', methods=['POST'])
    def home_set_light_dim():
        device_id = request.args.get('device_id')
        dim = int(round(float(request.args.get('dim'))))
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Light:
            raise TypeError("Can't set dimmer on device of type " + str(device.device_type))
        device.set_dim(dim, "user")
        return "OK"

    @staticmethod
    @app.route('/home/set_light_warmth', methods=['POST'])
    def home_set_light_warmth():
        device_id = request.args.get('device_id')
        warmth = int(round(float(request.args.get('warmth'))))
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Light:
            raise TypeError("Can't set warmth on device of type " + str(device.device_type))
        device.set_warmth(warmth, "user")
        return "OK"

    @staticmethod
    @app.route('/home/set_switch', methods=['POST'])
    def home_set_switch():
        device_id = request.args.get('device_id')
        active = request.args.get('state') == "true"
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Switch:
            raise TypeError("Can't set active on device of type " + str(device.device_type))
        device.set_active(active, "user")
        return "OK"

    @staticmethod
    @app.route('/home/set_group_state', methods=['POST'])
    def home_set_group_state():
        group_id = int(request.args.get('group_id'))
        active = request.args.get('state') == "true"
        group = DeviceController().get_group(group_id)
        group.set_state(active, "user")
        return "OK"

    @staticmethod
    @app.route('/home/set_group_dim', methods=['POST'])
    def home_set_group_dim():
        group_id = int(request.args.get('group_id'))
        dim = int(request.args.get('dim'))
        group = DeviceController().get_group(group_id)
        group.set_dim(dim, "user")
        return "OK"

    @staticmethod
    @app.route('/home/retry_connection', methods=['POST'])
    def home_retry_connection():
        Logger().write(LogVerbosity.Debug, "Retrying connection")
        id = request.args.get('id')
        device = DeviceController().get_device(id)
        device.accessible = device.initialize()
        return "OK"

    @staticmethod
    @app.route('/home/resync_provider', methods=['POST'])
    def home_resync_provider():
        Logger().write(LogVerbosity.Debug, "Resyncing provider")
        name = request.args.get('name')
        DeviceController().resync_provider_devices(name)
        return "OK"

    @staticmethod
    @app.route('/home/get_usage_stats', methods=['GET'])
    def home_usage_stats():
        type = request.args.get('type')
        start_time = int(request.args.get('startTime'))
        end_time = int(request.args.get('endTime'))
        interval = request.args.get('interval')

        device = DeviceController().get_devices_by_type(DeviceType.Thermostat)[0]
        stats = device.get_usage_stats(type, start_time, end_time, interval)
        return to_JSON(stats)

    @staticmethod
    @app.route('/home/moods', methods=['GET'])
    def home_moods():
        Logger().write(LogVerbosity.Debug, "Getting moods")
        return to_JSON(Database().get_moods())

    @staticmethod
    @app.route('/home/add_mood', methods=['POST'])
    def home_add_mood():
        Logger().write(LogVerbosity.Debug, "Adding mood")
        name = urllib.parse.unquote(request.args.get('name'))
        Database().add_mood(name)
        return "OK"

    @staticmethod
    @app.route('/home/remove_mood', methods=['POST'])
    def home_remove_mood():
        Logger().write(LogVerbosity.Debug, "Removing mood")
        id = int(request.args.get('id'))
        Database().remove_mood(id)
        RuleManager().mood_removed(id)
        return "OK"

    @staticmethod
    @app.route('/home/select_mood', methods=['POST'])
    def home_select_mood():
        Logger().write(LogVerbosity.Debug, "Selecting mood")
        id = int(request.args.get('id'))
        RuleManager().mood_selected(id)
        return "OK"


