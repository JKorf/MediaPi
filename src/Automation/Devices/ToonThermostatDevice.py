import random
import sys
import time

from toonapilib import Toon
import json

from Automation.DeviceBase import ThermostatDevice
from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread


class ToonThermostatDevice(ThermostatDevice):

    id = "ToonThermostat"

    def __init__(self, eneco_username, eneco_password, eneco_consumer_id, eneco_consumer_secret):
        super().__init__(ToonThermostatDevice.id, "Toon thermostat")
        self.__api = Toon(eneco_username, eneco_password, eneco_consumer_id, eneco_consumer_secret)
        self.setpoint = 0

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

    def set_setpoint(self, temperature):
        if self.testing:
            self.setpoint = temperature
            return

        for i in range(3):
            try:
                self.__api.thermostat = temperature
                self.setpoint = temperature
                Logger().write(LogVerbosity.Debug, "Temp set")
                Database().add_action_history("temperature", "set", "", temperature)
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