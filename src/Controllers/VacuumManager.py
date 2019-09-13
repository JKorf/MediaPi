from miio import Vacuum

from Database.Database import Database
from Shared.Settings import Settings
from Shared.Util import Singleton


class VacuumManager(metaclass=Singleton):

    def __init__(self):
        self.vacuum = Vacuum(Settings.get_string("vacuum_ip"))

    def start(self):
        Database().add_action_history("vacuum", "start", "user")
        self.vacuum.start()

    def home(self):
        Database().add_action_history("vacuum", "stop", "user")
        self.vacuum.home()

    def pause(self):
        Database().add_action_history("vacuum", "pause", "user")
        self.vacuum.pause()

