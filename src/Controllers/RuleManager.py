import time
from datetime import datetime, timedelta
from threading import Event

import math

from Automation.DeviceBase import DeviceType
from Automation.DeviceController import DeviceController
from Controllers.PresenceManager import PresenceManager
from Controllers.TVManager import TVManager
from Database.Database import Database
from Shared.Logger import LogVerbosity, Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import Singleton, current_time, add_leading_zero


class Rule:

    def __init__(self, id, name, created, active, last_execution):
        self.id = id
        self.last_check_time = 0
        self.created = created
        self.last_execution = last_execution
        self.active = active
        self.conditions = []
        self.actions = []
        self.name = name
        self.description = None

    def add_action(self, id, type, parameters):
        self.actions.append(RuleManager.actions[type](id, type, *parameters))
        self.description = self.get_description()

    def add_condition(self, id, type, parameters):
        self.conditions.append(RuleManager.conditions[type](id, type, *parameters))
        self.description = self.get_description()

    def check(self):
        should_execute = True
        for condition in self.conditions:
            if not condition.check():
                should_execute = False

        return should_execute

    def execute(self):
        for action in self.actions:
            action.execute()
        for condition in [x for x in self.conditions if x.name == "Mood select"]:
            condition.mood_selected = False
        self.last_execution = current_time()

    def get_description(self):
        result = "If "

        for condition in self.conditions:
            result += condition.get_description() + " and "

        result = result[:-4]
        result += "then "
        for action in self.actions:
            result += action.get_description() + " and "
        result = result[:-4]

        return result


class IsBetweenTimeCondition:
    name = "Time between"
    parameter_descriptions = [("Start time", "time"), ("End time", "time")]
    description = "Triggers when time is between 2 points"

    def __init__(self, id, type, start_time, end_time):
        self.id = id
        self.type = type
        self.start_time_hours = math.floor(int(start_time) / 60)
        self.start_time_minutes = int(start_time) % 60
        self.end_time_hours = math.floor(int(end_time) / 60)
        self.end_time_minutes = int(end_time) % 60
        self.parameters = [int(start_time), int(end_time)]

        self._next_start_time = RuleManager.update_check_time(self.start_time_hours, self.start_time_minutes)
        self._next_end_time = RuleManager.update_check_time(self.end_time_hours, self.end_time_minutes)
        if self._next_end_time < self._next_start_time:
            self._next_end_time += timedelta(days=1)

    def check(self):
        now = datetime.now()
        if now > self._next_end_time:
            self._next_start_time = RuleManager.update_check_time(self.start_time_hours, self.start_time_minutes)
            self._next_end_time = RuleManager.update_check_time(self.end_time_hours, self.end_time_minutes)

        result = self._next_start_time < now < self._next_end_time
        return result

    def get_description(self):
        return "time is between " + add_leading_zero(self.start_time_hours)+":" + add_leading_zero(self.start_time_minutes) + " and " + add_leading_zero(self.end_time_hours)+":" + add_leading_zero(self.end_time_minutes)


class MoodSelectCondition:
    name = "Mood select"
    parameter_descriptions = [("Mood", "mood")]
    description = "Triggers on a mood selection"

    def __init__(self, id, type, mood_id):
        self.id = id
        self.type = type
        self.mood_id = mood_id
        self.parameters = [int(mood_id)]
        self.mood_selected = False

    def check(self):
        return self.mood_selected

    def get_description(self):
        return "user selects mood " + str(self.mood_id)


class IsPassingTimeCondition:
    name = "Time passing"
    parameter_descriptions = [("Time trigger", "time")]
    description = "Triggers at a specific time"

    def __init__(self, id, type, trigger_time):
        self.id = id
        self.type = type
        self.time_hour = math.floor(int(trigger_time) / 60)
        self.time_minute = int(trigger_time) % 60
        self.parameters = [int(trigger_time)]

        self._next_check_time = RuleManager.update_check_time(self.time_hour, self.time_minute)

    def check(self):
        result = datetime.now() > self._next_check_time
        if result:
            self._next_check_time = RuleManager.update_check_time(self.time_hour, self.time_minute)
        return result

    def get_description(self):
        return "time is " + add_leading_zero(self.time_hour)+":" + add_leading_zero(self.time_minute)


class IsHomeCondition:
    name = "Is anyone home"
    parameter_descriptions = [("Anyone home", "bool")]
    description = "Triggers if people are home (or not)"

    def __init__(self, id, type, should_be_home):
        self.id = id
        self.type = type
        value = should_be_home == "True" or should_be_home == "true" or should_be_home == "1" or should_be_home is True
        self.parameters = [value]
        self.should_be_home = value

    def check(self):
        return PresenceManager().anyone_home == self.should_be_home

    def get_description(self):
        if self.should_be_home:
            return "someone is home"
        return "no one is home"


class OnLeavingHomeCondition:
    name = "On leaving home"
    parameter_descriptions = []
    description = "Triggers when everyone left home"

    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.parameters = []
        self.last_home_check = False

    def check(self):
        current_state = PresenceManager().anyone_home
        if not current_state and self.last_home_check:
            self.last_home_check = current_state
            return True
        self.last_home_check = current_state
        return False

    def get_description(self):
        return "last person left home"


class OnComingHomeCondition:
    name = "On coming home"
    parameter_descriptions = []
    description = "Triggers when someone comes home"

    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.parameters = []
        self.last_home_check = False

    def check(self):
        new_check = PresenceManager().anyone_home
        old_check = self.last_home_check
        self.last_home_check = new_check
        if new_check and not old_check:
            return True
        return False

    def get_description(self):
        return "first person comes home"


class DimDeviceGroupAction:

    name = "Set dimmer device group"
    description = "Set the dimmer for a device group to a specific value"
    parameter_descriptions = [("Group", "device_group"), ("Dim", "int")]

    def __init__(self, id, type, group_ids, dim):
        self.id = id
        self.type = type
        dim_value = int(dim)
        self.parameters = [group_ids, dim_value]
        self.group_ids = group_ids.split('|')
        self.dim = dim_value

    def execute(self):
        for group_id in self.group_ids:
            DeviceController().get_group(int(group_id)).set_dim(self.dim, "rule")

    def get_description(self):
        return "set the dimmer for device group " + str(self.parameters[0]) + " to " + str(self.dim) + "%"


class ToggleDeviceGroupAction:

    name = "Toggle a device group"
    description = "Turns a device group on or off"
    parameter_descriptions = [("Group", "device_group"), ("On/Off", "bool")]

    def __init__(self, id, type, group_ids, on):
        self.id = id
        self.type = type
        on_value = on == "True" or on == "true" or on == "1" or on is True
        self.parameters = [group_ids, on_value]
        self.group_ids = group_ids.split('|')
        self.on = on_value

    def execute(self):
        for group_id in self.group_ids:
            DeviceController().get_group(int(group_id)).set_state(self.on, "rule")

    def get_description(self):
        if self.on:
            return "turn on the devices for device group " + str(self.parameters[0])
        return "turn off the devices for device group " + str(self.parameters[0])


class DimDeviceAction:

    name = "Set dimmer device"
    description = "Set the dimmer for a device to a specific value"
    parameter_descriptions = [("Device", "device"), ("Dim", "int")]

    def __init__(self, id, type, device_ids, dim):
        self.id = id
        self.type = type
        dim_value = int(dim)
        self.parameters = [device_ids, dim_value]
        self.device_ids = device_ids.split('|')
        self.dim = dim_value

    def execute(self):
        for device_id in self.device_ids:
            device = DeviceController().get_device(device_id)
            if device.device_type == DeviceType.Light and device.can_dim:
                device.set_dim(self.dim, "rule")

    def get_description(self):
        return "set the dimmer for device " + str(self.parameters[0]) + " to " + str(self.dim) + "%"


class ToggleDeviceAction:

    name = "Toggle a device"
    description = "Turns a device on or off"
    parameter_descriptions = [("Device", "device"), ("On/Off", "bool")]

    def __init__(self, id, type, device_ids, on):
        self.id = id
        self.type = type
        on_value = on == "True" or on == "true" or on == "1" or on is True
        self.parameters = [device_ids, on_value]
        self.device_ids = device_ids.split('|')
        self.on = on_value

    def execute(self):
        for device_id in self.device_ids:
            device = DeviceController().get_device(device_id)
            if device.device_type == DeviceType.Switch:
                device.set_active(self.on, "rule")
            elif device.device_type == DeviceType.Light:
                device.set_on(self.on, "rule")

    def get_description(self):
        if self.on:
            return "turn on device " + str(self.parameters[0])
        return "turn off device " + str(self.parameters[0])


class SetDeviceTemperatureAction:

    name = "Set temperature"
    description = "Sets the temperature"
    parameter_descriptions = [("Device", "thermostat_device"), ("Target temperature", "int")]

    def __init__(self, id, type, device_ids, temp):
        self.id = id
        self.type = type
        self.parameters = [device_ids, temp]
        self.device_ids = device_ids.split('|')
        self.temp = int(temp)

    def execute(self):
        for device_id in self.device_ids:
            DeviceController().get_device(device_id).set_setpoint(self.temp, "rule")

    def get_description(self):
        return "set the temperature of device " + str(self.parameters[0]) + " to " + str(self.temp) + "°C"


class ToggleTvAction:

    name = "Turn on/off TV"
    description = "Turn the TV on or off"
    parameter_descriptions = [("Instance", "instance"), ("On/Off", "bool")]

    def __init__(self, id, type, instance, on):
        self.id = id
        self.type = type
        on_value = on == "True" or on == "true" or on == "1" or on is True
        self.parameters = [instance, on_value]
        self.instance = int(instance)
        self.on = on_value

    def execute(self):
        # TODO slave?
        if self.on:
            TVManager().turn_tv_on()
            TVManager().switch_input_to_pi()
        else:
            TVManager().turn_tv_off()

    def get_description(self):
        if self.on:
            return "turn on the tv"
        return "turn off the tv"


class PlayRadioAction:

    name = "Play radio"
    description = "Play radio"
    parameter_descriptions = [("Instance", "instance"), ("Channel", "radio")]

    def __init__(self, id, type, instance, channel):
        self.id = id
        self.type = type
        self.parameters = [instance, channel]
        self.instance = int(instance)
        self.channel = int(channel)

    def execute(self):
        # TODO slave?
        radio = [x for x in Database().get_radios() if x.id == self.channel][0]
        from MediaPlayer.MediaManager import MediaManager
        MediaManager().start_radio(radio.title, radio.url)

    def get_description(self):
        return "play a radio channel"


class RuleManager(metaclass=Singleton):
    conditions = {
        1: IsBetweenTimeCondition,
        2: IsPassingTimeCondition,
        3: IsHomeCondition,
        4: OnLeavingHomeCondition,
        5: OnComingHomeCondition,
        6: MoodSelectCondition
    }
    actions = {
        1: ToggleDeviceAction,
        2: ToggleDeviceGroupAction,
        3: SetDeviceTemperatureAction,
        4: ToggleTvAction,
        5: PlayRadioAction,
        6: DimDeviceAction,
        7: DimDeviceGroupAction
    }

    def __init__(self):
        self.running = False
        self.current_rules = []
        self.check_thread = CustomThread(self.check_rules, "Rule checker")
        self.load_rules()
        enabled = Database().get_stat("rules_enabled")
        self.enabled = bool(enabled)
        self.wait_event = Event()

    def start(self):
        if Settings.get_bool("slave"):
            return

        self.running = True
        self.check_thread.start()

    def mood_selected(self, id):
        for rule in self.current_rules:
            for condition in [x for x in rule.conditions if x.name == "Mood select"]:
                condition.mood_selected = int(condition.mood_id) == id

        self.wait_event.set()

    def device_group_removed(self, id):
        # TODO
        pass

    def mood_removed(self, id):
        # TODO
        pass

    def stop(self):
        self.running = False
        self.check_thread.join()

    def set_enabled(self, enabled):
        self.enabled = enabled
        Database().update_stat("rules_enabled", enabled)

    def check_rules(self):
        while self.running:
            Logger().write(LogVerbosity.All, "Checking rules")
            for rule in self.current_rules:
                if rule.check():
                    Logger().write(LogVerbosity.Info, "Executing rule " + rule.name + ": " + rule.description)
                    if self.enabled:
                        try:
                            rule.execute()
                        except Exception as e:
                            Logger().write_error(e, "Rule error")
                    Database().update_rule(rule)

            self.wait_event.wait(10)
            self.wait_event.clear()

    def update_rule(self, rule_id, active, name, actions, conditions):
        if rule_id == -1:
            rule = Rule(-1, name, current_time(), True, 0)
            self.current_rules.append(rule)
        else:
            rule = [x for x in self.current_rules if x.id == rule_id][0]
        rule.name = name
        rule.active = active
        rule.actions = []
        for action in actions:
            rule.add_action(-1, action[0], [x for x in action[1:] if x is not None])

        rule.conditions = []
        for condition in conditions:
            rule.add_condition(-1, condition[0], [x for x in condition[1:] if x is not None])

        rule.last_execution = 0
        Database().save_rule(rule)

    def remove_rule(self, rule_id):
        self.current_rules = [x for x in self.current_rules if x.id != rule_id]
        Database().remove_rule(rule_id)

    def get_rule(self, rule_id):
        return [x for x in self.current_rules if x.id == rule_id][0]

    def get_rules(self):
        return self.enabled, self.current_rules

    def get_actions_and_conditions(self):
        actions = [ActionModel(id, action.name, action.description, action.parameter_descriptions) for id, action in self.actions.items()]
        conditions = [ActionModel(id, condition.name, condition.description, condition.parameter_descriptions) for id, condition in self.conditions.items()]
        return actions, conditions

    def load_rules(self):
        db_rules = Database().get_rules()
        self.current_rules = self.parse_rules(db_rules)

    def parse_rules(self, rules):
        result = []
        for r in rules:
            rule = Rule(r.id, r.name, r.created, r.active, r.last_execution)
            for link in r.links:
                if link.rule_link_type == "Condition":
                    rule.add_condition(link.id, link.link_type, link.parameters)
                else:
                    rule.add_action(link.id, link.link_type, link.parameters)
            result.append(rule)
        return result

    @staticmethod
    def update_check_time(hour, minute):
        result = datetime.now()
        if result.hour > hour or (result.hour == hour and result.minute >= minute):
            result += timedelta(days=1)
        result = result.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return result


class ActionModel:

    def __init__(self, id, name, description, parameter_descriptions):
        self.id = id
        self.name = name
        self.description = description
        self.parameter_description = parameter_descriptions
