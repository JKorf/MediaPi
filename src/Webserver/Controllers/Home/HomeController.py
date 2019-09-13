from flask import request

from Automation.DeviceBase import DeviceType
from Automation.DeviceController import DeviceController
from Shared.Util import to_JSON
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
        return "OK"

    @staticmethod
    @app.route('/home/set_setpoint', methods=['POST'])
    def home_set_temperature():
        device_id = request.args.get('device_id')
        temp = float(request.args.get('temperature'))
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Thermostat:
            raise TypeError("Can't set temperature on device of type " + str(device.device_type))

        device.set_setpoint(temp)
        return "OK"

    @staticmethod
    @app.route('/home/set_light_state', methods=['POST'])
    def home_set_light_state():
        device_id = request.args.get('device_id')
        on = request.args.get('state') == "true"
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Light:
            raise TypeError("Can't set light on device of type " + str(device.device_type))
        device.set_on(on)
        return "OK"

    @staticmethod
    @app.route('/home/set_light_dim', methods=['POST'])
    def home_set_light_dim():
        device_id = request.args.get('device_id')
        dim = int(request.args.get('dim'))
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Light:
            raise TypeError("Can't set dimmer on device of type " + str(device.device_type))
        device.set_dimmer(dim)
        return "OK"

    @staticmethod
    @app.route('/home/set_light_warmth', methods=['POST'])
    def home_set_light_warmth():
        device_id = request.args.get('device_id')
        warmth = int(request.args.get('warmth'))
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Light:
            raise TypeError("Can't set warmth on device of type " + str(device.device_type))
        device.set_warmth(warmth)
        return "OK"

    @staticmethod
    @app.route('/home/set_switch', methods=['POST'])
    def home_set_switch():
        device_id = request.args.get('device_id')
        active = request.args.get('state') == "true"
        device = DeviceController().get_device(device_id)
        if device.device_type != DeviceType.Switch:
            raise TypeError("Can't set active on device of type " + str(device.device_type))
        device.set_active(active)
        return "OK"

    @staticmethod
    @app.route('/home/set_group', methods=['POST'])
    def home_set_group():
        group_id = int(request.args.get('group_id'))
        active = request.args.get('state') == "true"
        group = DeviceController().get_group(group_id)
        group.set_state(active)
        return "OK"
