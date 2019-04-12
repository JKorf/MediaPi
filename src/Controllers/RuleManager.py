import time
from datetime import datetime, timedelta

import math

from Controllers.LightManager import LightManager
from Controllers.PresenceManager import PresenceManager
from Controllers.ToonManager import ToonManager
from Database.Database import Database
from Shared.Logger import LogVerbosity, Logger
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
        self.run = False
        self.description = None

    def add_action(self, id, type, parameters):
        self.actions.append(RuleManager.actions[type](id, type, *parameters))
        self.description = self.get_description()

    def add_condition(self, id, type, parameters):
        self.conditions.append(RuleManager.conditions[type](id, type, *parameters))
        self.description = self.get_description()

    def check(self):
        for condition in self.conditions:
            if not condition.check():
                self.run = False
                return False

        return not self.run

    def execute(self):
        for action in self.actions:
            action.execute()
        self.last_execution = current_time()
        self.run = True

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
    description = "Is true when the time is between the start and end time"

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
        result = self._next_start_time < now < self._next_end_time
        if not result and now > self._next_end_time:
            self._next_start_time = RuleManager.update_check_time(self.start_time_hours, self.start_time_minutes)
            self._next_end_time = RuleManager.update_check_time(self.end_time_hours, self.end_time_minutes)

        return result

    def get_description(self):
        return "time is between " + add_leading_zero(self.start_time_hours)+":" + add_leading_zero(self.start_time_minutes) + " and " + add_leading_zero(self.end_time_hours)+":" + add_leading_zero(self.end_time_minutes)


class IsPassingTimeCondition:
    name = "Time passing"
    parameter_descriptions = [("Time trigger", "time")]
    description = "Is true the first time the current time passes the specified time"

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
    description = "Is true if anyone is home is equal to provided should_be_home"

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
    description = "Is true the first time when nobody is home after someone was home"

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
    description = "Is true the first time when someone is home after nobody was home"

    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.parameters = []
        self.last_home_check = False

    def check(self):
        current_state = PresenceManager().anyone_home
        if current_state and not self.last_home_check:
            self.last_home_check = current_state
            return True
        self.last_home_check = current_state
        return False

    def get_description(self):
        return "first person comes home"


class ToggleLightsAction:

    name = "Toggle lights"
    description = "Turn on or off the lights in the specified groups"
    parameter_descriptions = [("Light group", "light_group"), ("On/Off", "bool")]

    def __init__(self, id, type, group_ids, on):
        self.id = id
        self.type = type
        on_value = on == "True" or on == "true" or on == "1" or on is True
        self.parameters = [group_ids, on_value]
        self.group_ids = group_ids.split('|')
        self.on = on_value

    def execute(self):
        for group_id in self.group_ids:
            LightManager().set_group_state(group_id, self.on)

    def get_description(self):
        if self.on:
            return "turn on the lights for light group " + str(self.parameters[0])
        return "turn off the lights for light group " + str(self.parameters[0])


class SetTemperatureAction:

    name = "Set temperature"
    description = "Change the temperature"
    parameter_descriptions = [("Target temperature", "int")]

    def __init__(self, id, type, temp):
        self.id = id
        self.type = type
        self.parameters = [temp]
        self.temp = int(temp)

    def execute(self):
        pass
        #ToonManager().set_temperature(self.temp)

    def get_description(self):
        return "set the temperature to " + str(self.temp) + "°C"


class RuleManager(metaclass=Singleton):
    conditions = {
        1: IsBetweenTimeCondition,
        2: IsPassingTimeCondition,
        3: IsHomeCondition,
        4: OnLeavingHomeCondition,
        5: OnComingHomeCondition
    }
    actions = {
        1: ToggleLightsAction,
        2: SetTemperatureAction
    }

    def __init__(self):
        self.running = False
        self.current_rules = []
        self.check_thread = CustomThread(self.check_rules, "Rule checker")
        self.load_rules()

    def start(self):
        self.running = True
        self.check_thread.start()

    def stop(self):
        self.running = False
        self.check_thread.join()

    def check_rules(self):
        while self.running:
            Logger().write(LogVerbosity.All, "Checking rules")
            for rule in self.current_rules:
                if rule.check():
                    Logger().write(LogVerbosity.Info, "Executing rule " + rule.name + ": " + rule.description)
                    rule.execute()
                    Database().update_rule(rule)

            time.sleep(10)

    def update_rule(self, rule_id, active, name, actions, conditions):
        if rule_id == -1:
            rule = Rule(-1, name, current_time(), True)
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
        return self.current_rules

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
