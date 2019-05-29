import subprocess
import sys
import uuid

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Observable import Observable
from Shared.Settings import Settings, SecureSettings
from Shared.Threading import CustomThread
from Shared.Util import Singleton, current_time
from Webserver.Models import LightDevice, LightControl, SocketDevice, SocketControl, DeviceGroup


class TradfriManager(metaclass=Singleton):

    api_factory = None
    api = None
    gateway = None
    enabled = False
    initialized = False
    last_init = 0

    def __init__(self):
        self.tradfri_state = TradfriState()
        self.observing_end = 0
        self.observing = False
        self.observe_thread = None

    def init(self):
        if self.initialized:
            Logger().write(LogVerbosity.Info, "already init")
            return

        if sys.platform != "linux" and sys.platform != "linux2":
            Logger().write(LogVerbosity.Info, "Lighting: Not initializing, no coap client available on windows")
            self.initialized = True
            self.tradfri_state.update_group(DeviceGroup(1, "Test group", True, 128, 6))
            self.tradfri_state.update_group(DeviceGroup(2, "Test group 2", False, 18, 6))
            return

        if current_time() - self.last_init < 5000:
            Logger().write(LogVerbosity.Info, "Tried initialization less than 5s ago")
            return

        Logger().write(LogVerbosity.All, "Start LightManager init")
        self.enabled = True
        if not self.initialized:
            ip = Settings.get_string("tradfri_hub_ip")
            identity = Database().get_stat_string("LightingId")
            key = Database().get_stat_string("LightingKey")

            if identity is None or key is None:
                Logger().write(LogVerbosity.Info, "Lighting: No identity/key found, going to generate new")
                # We don't have all information to connect, reset and start from scratch
                Database().remove_stat("LightingId")
                Database().remove_stat("LightingKey")
                key = None

                identity = uuid.uuid4().hex
                Database().update_stat("LightingId", identity)  # Generate and save a new id
                self.api_factory = APIFactory(host=ip, psk_id=identity)
            else:
                self.api_factory = APIFactory(host=ip, psk_id=identity, psk=key)

            self.api = self.api_factory.request
            self.gateway = Gateway()

            if key is None:
                try:
                    security_code = SecureSettings.get_string("tradfri_hub_code")  # the code at the bottom of the hub
                    key = self.api_factory.generate_psk(security_code)
                    Database().update_stat("LightingKey", key)  # Save the new key
                    Logger().write(LogVerbosity.Info, "Lighting: New key retrieved")
                except Exception as e:
                    Logger().write_error(e, "Unhandled exception")
                    return
            else:
                Logger().write(LogVerbosity.Info, "Lighting: Previously saved key found")

            try:
                self.initialized = True
                groups = self.get_device_groups()
                for group in groups:
                    self.tradfri_state.update_group(group)
            except subprocess.TimeoutExpired as e:
                self.initialized = False
                Logger().write_error(e, "Failed to get groups from hub")

    def start_observing(self):
        Logger().write(LogVerbosity.Debug, "Start observing light data")
        self.observing = True
        if self.observing_end > current_time():
            Logger().write(LogVerbosity.All, "Still observing, not starting again")
            return  # still observing, the check observing thread will renew

        if not self.check_state():
            return

        self.observing_end = current_time() + 30000
        groups_commands = self.api(self.gateway.get_groups())
        result = self.api(groups_commands)
        for group in result:
            self.observe_group(group)

    def observe_group(self, group):
        Logger().write(LogVerbosity.All, "Starting observe for group " + group.name)
        self.observe_thread = CustomThread(lambda: self.api(group.observe(
            self.tradfri_state.update_group,
            lambda x: self.check_observe(group), duration=30)), "Light group observer", [])
        self.observe_thread.start()

    def check_observe(self, group):
        if self.observing:
            # Restart observing since it timed out
            Logger().write(LogVerbosity.Debug, "Restarting observing for group " + str(group.name))
            self.observe_group(group)

    def stop_observing(self):
        Logger().write(LogVerbosity.Debug, "Stop observing light data")
        self.observing = False

    def get_devices(self):
        if not self.check_state():
            return []

        Logger().write(LogVerbosity.All, "Get devices")
        devices_commands = self.api(self.gateway.get_devices())
        devices = self.api(devices_commands)
        return [d for d in [self.parse_device(x) for x in devices] if d is not None]

    def set_state(self, device_id, state):
        if not self.check_state():
            return

        Logger().write(LogVerbosity.All, "Set device state")
        device = self.api(self.gateway.get_device(device_id))
        if device.has_light_control:
            self.api(device.light_control.set_state(state))
        else:
            self.api(device.socket_control.set_state(state))

    def set_light_warmth(self, device_id, warmth):
        if not self.check_state():
            return

        Logger().write(LogVerbosity.All, "Set light warmth")
        device = self.api(self.gateway.get_device(device_id))
        self.api(device.light_control.set_color_temp(warmth))

    def set_light_dimmer(self, device_id, amount):
        if not self.check_state():
            return

        Logger().write(LogVerbosity.All, "Set light dimmer")
        device = self.api(self.gateway.get_device(device_id))
        self.api(device.light_control.set_dimmer(amount))

    def set_device_name(self, device_id, name):
        if not self.check_state():
            return

        Logger().write(LogVerbosity.All, "Set device name")
        device = self.api(self.gateway.get_device(device_id))
        self.api(device.set_name(name))

    def get_device_groups(self):
        if not self.check_state():
            return []

        Logger().write(LogVerbosity.All, "Get device groups")
        groups_commands = self.api(self.gateway.get_groups())
        result = self.api(groups_commands)
        Logger().write(LogVerbosity.All, "Get device groups: " + str([x.raw for x in result]))
        return [DeviceGroup(group.id, group.name, group.state, group.dimmer, len(group.member_ids)) for group in result]

    def get_devices_in_group(self, group):
        if not self.check_state():
            return []

        Logger().write(LogVerbosity.All, "Get lights in group")
        group = self.api(self.gateway.get_group(group))
        members = group.member_ids
        result = [self.api(self.gateway.get_device(x)) for x in members]
        return [d for d in [self.parse_device(x) for x in result] if d is not None]

    def set_group_name(self, group, name):
        if not self.check_state():
            return

        Logger().write(LogVerbosity.All, "Set group name")
        group = self.api(self.gateway.get_group(group))
        self.api(group.set_name(name))

    def set_group_state(self, group, state):
        if not self.check_state():
            return

        Logger().write(LogVerbosity.All, "Set group state")
        group = self.api(self.gateway.get_group(group))
        self.api(group.set_state(state))

    def set_group_dimmer(self, group, dimmer):
        if not self.check_state():
            return

        Logger().write(LogVerbosity.All, "Set group dimmer")
        group = self.api(self.gateway.get_group(group))
        self.api(group.set_dimmer(dimmer))

    def check_state(self):
        if not self.enabled:
            return False  # not available

        if not self.initialized:
            self.init()
            if not self.initialized:
                return False  # init failed
        return True

    @staticmethod
    def parse_device(data):
        if data.has_light_control:
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

        elif data.has_socket_control:
            sockets = []
            for socket in data.socket_control.sockets:
                sockets.append(SocketDevice(socket.state))

            return SocketControl(data.id, data.name, data.application_type, data.last_seen.timestamp(), data.reachable, sockets)


class TradfriState(Observable):

    def __init__(self):
        super().__init__("TradfriData", 1)
        self.groups = []

    def update_group(self, group):
        if hasattr(group, 'raw'):
            Logger().write(LogVerbosity.Debug, "Group update: " + str(group.raw))

        if group.id not in [x.id for x in self.groups]:
            if hasattr(group, 'device_count'):
                device_count = group.device_count
            else:
                device_count = len(group.member_ids)
            self.groups.append(DeviceGroup(group.id, group.name, group.state, group.dimmer, device_count))
        else:
            g = [x for x in self.groups if x.id == group.id][0]
            g.state = group.state
            g.dimmer = group.dimmer
        self.changed()

    def update_device(self, device):
        pass
