import subprocess
import sys

from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread
from Shared.Util import Singleton


class TVManager(metaclass=Singleton):

    # 0 - TV
    # 1,2 - Recording 1/2
    # 3,6,7,A - Tuner 1/2/3/4
    # 4,8,B - Playback 1/2/3

    def __init__(self):
        self.pi_source = "1"
        self.tv_source = "0"
        self.debug_level = "1"
        self.cec_process = None
        self.pi_is_active = False
        self.pi = sys.platform == "linux" or sys.platform == "linux2"

    def switch_input_to_pi(self):
        if not self.pi or self.pi_is_active:
            return

        self.pi_is_active = True
        self.__request('as')

    def switch_input_to_tv(self):
        if not self.pi or not self.pi_is_active:
            return

        self.pi_is_active = False
        self.__request('is')

    def turn_tv_on(self):
        if not self.pi:
            return

        self.__request('on ' + self.tv_source)

    def turn_tv_off(self):
        if not self.pi:
            return

        self.__request('standby ' + self.tv_source)

    def __read_cec(self):
        for line in iter(self.cec_process.stdout.readline, b''):
            Logger().write(LogVerbosity.All, "CEC: " + line.decode('utf-8'))

    def start(self):
        if not self.pi:
            return

        self.cec_process = subprocess.Popen(['cec-client', '-u'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t = CustomThread(self.__read_cec, "Cec reader", [])
        t.start()

    @staticmethod
    def __construct_request(source, destination, command):
        return 'echo "tx ' + source + destination + ":" + command + '" | cec-client -s'

    def __request(self, command):
        Logger().write(LogVerbosity.Debug, "TV manager sending command: " + command)
        self.cec_process.stdin.write(command.encode('utf-8') + b'\n')
        self.cec_process.stdin.flush()
