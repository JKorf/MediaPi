from toonapilib import Toon

from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import SecureSettings
from Shared.Util import Singleton


class ToonManager(metaclass=Singleton):

    def __init__(self):
        self.api = Toon(SecureSettings.get_string("eneco_username"), SecureSettings.get_string("eneco_pw"), SecureSettings.get_string("toon_consumer_id"), SecureSettings.get_string("toon_consumer_secret"))

    def get_status(self):
        Logger().write(LogVerbosity.All, "Get toon status")
        return self.api.thermostat_info

    def get_states(self):
        Logger().write(LogVerbosity.All, "Get toon states")
        return self.api.thermostat_states

    def set_temperature(self, temp):
        Logger().write(LogVerbosity.Debug, "Set toon temperature: " + str(temp))
        self.api.thermostat = temp

    def set_state(self, state):
        Logger().write(LogVerbosity.Debug, "Set toon state:" + str(state))
        self.api.thermostat_state = state
