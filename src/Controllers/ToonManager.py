from toonapilib import Toon

from Shared.Settings import Settings
from Shared.Util import Singleton


class ToonManager(metaclass=Singleton):

    def __init__(self):
        self.api = Toon(Settings.get_string("eneco_username"), Settings.get_string("eneco_pw"), Settings.get_string("toon_consumer_id"), Settings.get_string("toon_consumer_secret"))

    def get_status(self):
        return self.api.thermostat_info

    def set_temperature(self, temp):
        self.api.thermostat = temp