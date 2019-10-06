import random
import time

import math
from toonapilib import Toon
import json

from Automation.DeviceBase import ThermostatDevice
from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread
from Shared.Util import current_time


class ToonThermostatDevice(ThermostatDevice):
    id = "ToonThermostat"

    def __init__(self, testing, eneco_username, eneco_password, eneco_consumer_id, eneco_consumer_secret):
        super().__init__("ToonThermostat", ToonThermostatDevice.id, "Toon thermostat", testing, True, None)
        if not testing:
            self.__api = Toon(eneco_username, eneco_password, eneco_consumer_id, eneco_consumer_secret)
        self.setpoint = 0
        self.eneco_username = eneco_username
        self.eneco_password = eneco_password
        self.eneco_consumer_id = eneco_consumer_id
        self.eneco_consumer_secret = eneco_consumer_secret

        self.__usage_data_buffers = \
            dict(gas=dict(minutes=UsageDataBuffer(60 * 5),
                          hours=UsageDataBuffer(60 * 60),
                          days=UsageDataBuffer(60 * 60 * 24),
                          months=UsageDataBuffer(60 * 60 * 24 * 30),
                          years=UsageDataBuffer(60 * 60 * 24 * 365)),

                 power=dict(minutes=UsageDataBuffer(60 * 5),
                            hours=UsageDataBuffer(60 * 60),
                            days=UsageDataBuffer(60 * 60 * 24),
                            months=UsageDataBuffer(60 * 60 * 24 * 30),
                            years=UsageDataBuffer(60 * 60 * 24 * 365)))

    def initialize(self):
        thermostat_info = self.get_temperature()
        if thermostat_info is None:
            return False

        self.temperature = thermostat_info.current_displayed_temperature / 100
        self.setpoint = thermostat_info.current_set_point / 100
        if self.testing:
            t = CustomThread(self.random_change, "Thermostat device changer", [])
            t.start()
        return True

    def deinitialize(self):
        # might need to implement this at some point
        pass

    def update(self, temperature, setpoint):
        self.temperature = temperature
        self.setpoint = setpoint

    def set_setpoint(self, temperature, src):
        if self.testing:
            Database().add_action_history(self.id, "temperature", src, temperature)
            self.setpoint = temperature
            return

        for i in range(3):
            try:
                self.__api.thermostat = temperature
                self.setpoint = temperature
                Logger().write(LogVerbosity.Debug, "Temp set")
                Database().add_action_history(self.id, "temperature", src, temperature)
                return
            except json.decoder.JSONDecodeError as e:
                Logger().write(LogVerbosity.Info, "Toon set temp error, try " + str(i + 1))
                if i == 2:
                    Logger().write_error(e, "Toon set temp error")
                time.sleep(1)

    def get_temperature(self):
        if self.testing:
            result = Obj()
            result.current_displayed_temperature = 2000
            result.current_set_point = 2000
            return result

        Logger().write(LogVerbosity.All, "Get toon status")
        result = None
        for i in range(3):
            try:
                result = self.__api.thermostat_info
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Toon thermostat_info failed attempt " + str(i) + ": " + str(e))

            if result is not None:
                return result
            time.sleep(1)
        return None

    def get_usage_stats(self, type, start_time, end_time, interval):
        Logger().write(LogVerbosity.All, "Get toon gas stats")
        if self.testing:
            return None

        start_string = str(start_time)
        end_string = str(end_time)

        buffered_data = self.__usage_data_buffers[type][interval].get_data(start_time, end_time)
        if buffered_data is not None:
            Logger().write(LogVerbosity.Debug,
                           "Returning buffered " + type + " usage data from " + start_string + " till " + end_string)
            return buffered_data

        self.__usage_data_buffers[type][interval].clean_data()

        for i in range(3):
            try:
                Logger().write(LogVerbosity.Debug,
                               "Retrieving " + type + " usage data from " + start_string + " till " + end_string)
                if interval != "minutes":
                    if type == "gas":
                        result = self.__api.data.graph.get_gas_time_window(start_string, end_string, interval)
                    else:
                        result = self.__api.data.graph.get_power_time_window(start_string, end_string, interval)
                        for data in result[interval]:
                            data['value'] = data['peak'] + data['offPeak']

                    for data in result[interval]:
                        if data['value'] < 0:
                            result[interval].remove(data)

                    self.__usage_data_buffers[type][interval].add_data(result[interval])
                    return result[interval]
                else:
                    if type == "gas":
                        result = self.__api.data.flow.get_gas_time_window(start_string, end_string)
                    else:
                        result = self.__api.data.flow.get_power_time_window(start_string, end_string)

                    for data in result['hours']:
                        if data['value'] < 0:
                            result['hours'].remove(data)

                    self.__usage_data_buffers[type][interval].add_data(result["hours"])
                    return result['hours']
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Toon get_usage_stats failed attempt " + str(i) + ": " + str(e))

            time.sleep(1)
        return None

    def random_change(self):
        while True:
            up = bool(random.getrandbits(1))
            if up:
                self.temperature += 1
            else:
                self.temperature -= 1

            time.sleep(5)


class Obj:

    def __init__(self):
        pass


class UsageDataBuffer:

    def __init__(self, interval):
        self.interval = interval
        self.data = []

    def get_data(self, start_time, end_time):
        data = [x for x in self.data if start_time <= x.timestamp < end_time]
        expected_items = math.ceil((end_time - start_time) / 1000 / self.interval)
        if expected_items != len(data):
            return None

        for x in data:
            x.last_access = current_time()
        return sorted([x.data for x in data], key=lambda x: x['timestamp'])

    def add_data(self, data):
        added = 0
        for record in [x for x in data if len([y for y in self.data if y.timestamp == x['timestamp']]) == 0]:
            if ((current_time() - record['timestamp']) / 1000) < self.interval:
                Logger().write(LogVerbosity.Debug, "Not adding timestamp " + str(record['timestamp']) + " since its not complete yet")
                continue
            self.data.append(UsageData(record['timestamp'], record))
            added += 1
        Logger().write(LogVerbosity.Debug, "Added " + str(added) + " item to usage buffer")

    def clean_data(self):
        old = len(self.data)
        self.data = [x for x in self.data if current_time() - x.last_access < 1000 * 60 * 60 * 24 * 7]
        change = old - len(self.data)
        if change > 0:
            Logger().write(LogVerbosity.Debug, "Cleaned " + str(change) + " items from usage buffer")


class UsageData:

    def __init__(self, timestamp, data):
        self.timestamp = timestamp
        self.data = data
        self.last_access = current_time()
