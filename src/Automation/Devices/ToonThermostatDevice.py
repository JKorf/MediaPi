import random
import sys
import time

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
        super().__init__("ToonThermostat", ToonThermostatDevice.id, "Toon thermostat", testing, True)
        if not testing:
            self.__api = Toon(eneco_username, eneco_password, eneco_consumer_id, eneco_consumer_secret)
        self.setpoint = 0
        self.eneco_username = eneco_username
        self.eneco_password = eneco_password
        self.eneco_consumer_id = eneco_consumer_id
        self.eneco_consumer_secret = eneco_consumer_secret

        self.__last_gas_usage_data = (0, None)
        self.__last_power_usage_data = (0, None)

    def initialize(self):
        thermostat_info = self.get_temperature()
        self.temperature = thermostat_info.current_displayed_temperature
        self.setpoint = thermostat_info.current_set_point
        if sys.platform != "linux" and sys.platform != "linux2":
            t = CustomThread(self.random_change, "Thermostat device changer", [])
            t.start()

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
            result.current_displayed_temperature = 20
            result.current_set_point = 20
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

    def get_gas_stats(self, from_date, to_date, interval):
        Logger().write(LogVerbosity.All, "Get toon gas stats")
        result = None

        if self.testing:
            return None

        if current_time() - self.__last_gas_usage_data[0] < 1000 * 60 * 5:
            return self.__last_gas_usage_data[1]

        for i in range(3):
            try:
                result = self.__api.data.graph.get_gas_time_window(from_date, to_date, interval)
                self.__last_gas_usage_data = (current_time(), result)
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Toon get_gas_stats failed attempt " + str(i) + ": " + str(e))

            if result is not None:
                return result
            time.sleep(1)
        return None

    def get_electricity_stats(self, from_date, to_date):
        Logger().write(LogVerbosity.All, "Get toon electricity stats")
        result = None

        if self.testing:
            return None

        if current_time() - self.__last_power_usage_data[0] < 1000 * 60 * 5:
            return self.__last_power_usage_data[1]

        for i in range(3):
            try:
                result = self.__api.data.flow.get_power_time_window(from_date, to_date)
                self.__last_power_usage_data = (current_time(), result)
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Toon get_electricity_stats failed attempt " + str(i) + ": " + str(e))

            if result is not None:
                return result
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