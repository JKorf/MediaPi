import psutil
import time

from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import Singleton


class StateManager(metaclass=Singleton):

    def __init__(self):
        self.state_data = StateData()
        self.state_data.name = Settings.get_string("name")
        self.watch_thread = CustomThread(self.update_state, "State observer")
        self.watch_thread.start()

    def update_state(self):
        while True:
            self.state_data.start_update()
            self.state_data.memory = psutil.virtual_memory().percent
            self.state_data.cpu = psutil.cpu_percent()
            self.state_data.threads = ThreadManager.thread_count()
            self.state_data.stop_update()
            time.sleep(1)


class StateData(Observable):

    def __init__(self):
        super().__init__("StateData", 1)
        self.name = None
        self.memory = 0
        self.cpu = 0
        self.threads = 0