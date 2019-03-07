import sys
import traceback
import uuid
from threading import Lock

import time
from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory

from Database.Database import Database
from Shared.Logger import Logger
from Shared.Observable import Observable
from Shared.Settings import Settings, SecureSettings
from Shared.Threading import CustomThread
from Shared.Util import Singleton, current_time
from Webserver.Models import LightGroup, LightDevice, LightControl


class LightManager(metaclass=Singleton):

    api_factory = None
    api = None
    gateway = None
    enabled = False
    initialized = False
    init_lock = Lock()

    def __init__(self):
        self.light_state = LightState()
        self.observing_end = 0
        self.observing = False

    def init(self):
        if self.initialized:
            Logger().write(2, "already init")
            return

        with self.init_lock:
            if sys.platform != "linux" and sys.platform != "linux2":
                Logger().write(2, "Lighting: Not initializing, no coap client available on windows")
                self.initialized = True
                self.light_state.update_group(LightGroup(1, "Test group", True, 128))
                self.light_state.update_group(LightGroup(2, "Test group 2", False, 18))
                return

            self.enabled = True
            if not self.initialized:
                ip = Settings.get_string("tradfri_hub_ip")
                identity = Database().get_stat_string("LightingId")
                key = Database().get_stat_string("LightingKey")

                if identity is None or key is None:
                    Logger().write(2, "Lighting: No identity/key found, going to generate new")
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
                        Logger().write(2, "Lighting: New key retrieved")
                        self.initialized = True
                    except Exception:
                        stack_trace = traceback.format_exc().split('\n')
                        for stack_line in stack_trace:
                            Logger().write(3, stack_line)
                        return
                else:
                    Logger().write(2, "Lighting: Previously saved key found")
                    self.initialized = True

                groups = self.get_light_groups()
                for group in groups:
                    self.light_state.update_group(group)

    def start_observing(self):
        Logger().write(2, "Start observing light data")
        self.observing = True
        if self.observing_end > current_time():
            return # still observing, the check observing thread will renew

        if not self.check_state():
            return

        self.observing_end = current_time() + 30000
        groups_commands = self.api(self.gateway.get_groups())
        result = self.api(groups_commands)
        for group in result:
            self.observe_group(group)

    def observe_group(self, group):
        observe_thread = CustomThread(lambda: self.api(group.observe(
            self.light_state.update_group,
            lambda x: self.check_observe(group), duration=30)), "Light group observer", [])
        observe_thread.start()

    def check_observe(self, group):
        if self.observing:
            # Restart observing since it timed out
            Logger().write(2, "Restarting observing for group " + str(group.name))
            self.observe_group(group)

    def stop_observing(self):
        Logger().write(2, "Stop observing light data")
        self.observing = False

    def get_lights(self):
        if not self.check_state():
            return []

        devices_commands = self.api(self.gateway.get_devices())
        lights = self.api(devices_commands)
        [self.parse_light_control(x) for x in lights if x.has_light_control]

    def set_light_state(self, light, state):
        if not self.check_state():
            return

        device = self.api(self.gateway.get_device(light))
        self.api(device.light_control.set_state(state))

    def set_light_warmth(self, light, warmth):
        if not self.check_state():
            return

        device = self.api(self.gateway.get_device(light))
        self.api(device.light_control.set_color_temp(warmth))

    def set_light_dimmer(self, light, amount):
        if not self.check_state():
            return

        device = self.api(self.gateway.get_device(light))
        self.api(device.light_control.set_dimmer(amount))

    def set_light_name(self, light, name):
        if not self.check_state():
            return

        device = self.api(self.gateway.get_device(light))
        self.api(device.set_name(name))

    def get_light_groups(self):
        if not self.check_state():
            return []

        groups_commands = self.api(self.gateway.get_groups())
        result = self.api(groups_commands)
        Logger().write(2, "Get light groups 2: " + str([x.raw for x in result]))
        return [LightGroup(group.id, group.name, group.state, group.dimmer) for group in result]

    def get_lights_in_group(self, group):
        if not self.check_state():
            return []

        group = self.api(self.gateway.get_group(group))
        members = group.member_ids
        result = [self.api(self.gateway.get_device(x)) for x in members]
        return [self.parse_light_control(x) for x in result if x.has_light_control]

    def set_group_name(self, group, name):
        if not self.check_state():
            return

        group = self.api(self.gateway.get_group(group))
        self.api(group.set_name(name))

    def set_group_state(self, group, state):
        if not self.check_state():
            return

        group = self.api(self.gateway.get_group(group))
        self.api(group.set_state(state))

    def set_group_dimmer(self, group, dimmer):
        if not self.check_state():
            return

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

class LightState(Observable):

    def __init__(self):
        super().__init__("LightData", 1)
        self.groups = []
        self._update_lock = Lock()

    def update_group(self, group):
        if hasattr(group, 'raw'):
            Logger().write(2, "Light update: " + str(group.raw))
        with self._update_lock:
            if not group.id in [x.id for x in self.groups]:
                self.groups.append(LightGroup(group.id, group.name, group.state, group.dimmer))
            else:
                g = [x for x in self.groups if x.id == group.id][0]
                g.state = group.state
                g.dimmer = group.dimmer
            self.changed()

    def update_device(self, device):
        pass