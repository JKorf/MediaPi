import json
import time

from toonapilib import Toon

from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import SecureSettings
from Shared.Util import Singleton


class ToonManager(metaclass=Singleton):

    def __init__(self):
        self.api = Toon(SecureSettings.get_string("eneco_username"), SecureSettings.get_string("eneco_pw"), SecureSettings.get_string("toon_consumer_id"), SecureSettings.get_string("toon_consumer_secret"))

    def get_status(self):
        Logger().write(LogVerbosity.All, "Get toon status")
        result = None
        for i in range(3):
            try:
                result = self.api.thermostat_info
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Toon thermostat_info failed attempt " + str(i) + ": " + str(e))

            if result is not None:
                return result
            time.sleep(1)
        return None

    def get_states(self):
        Logger().write(LogVerbosity.All, "Get toon states")
        return self.api.thermostat_states

    def set_temperature(self, temp):
        Logger().write(LogVerbosity.Debug, "Set toon temperature: " + str(temp))
        for i in range(3):
            try:
                self.api.thermostat = temp
                return
            except json.decoder.JSONDecodeError as e:
                Logger().write_error(e, "Toon set temp error, try " + str(i + 1))
                time.sleep(1)

    def set_state(self, state):
        Logger().write(LogVerbosity.Debug, "Set toon state:" + str(state))
        self.api.thermostat_state = state

    def get_gas_stats(self, from_date, to_date, interval):
        Logger().write(LogVerbosity.All, "Get toon gas stats")
        result = None
        for i in range(3):
            try:
                result = self.api.data.graph.get_gas_time_window(from_date, to_date, interval)
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Toon get_gas_stats failed attempt " + str(i) + ": " + str(e))

            if result is not None:
                return result
            time.sleep(1)
        return None

    def get_electricity_stats(self, from_date, to_date):
        Logger().write(LogVerbosity.All, "Get toon electricity stats")
        result = None
        for i in range(3):
            try:
                result = self.api.data.flow.get_power_time_window(from_date, to_date)
            except Exception as e:
                Logger().write(LogVerbosity.Info, "Toon get_electricity_stats failed attempt " + str(i) + ": " + str(e))

            if result is not None:
                return result
            time.sleep(1)
        return None