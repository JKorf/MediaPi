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
        self.key_callbacks = []
        self.last_action_id = 0

    def on_key_press(self, key, callback):
        self.key_callbacks.append(KeyCallback(key, callback))

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
            self.parse_cec_line(line.decode('utf-8'))

    def parse_cec_line(self, line):
        Logger().write(LogVerbosity.All, "CEC: " + line)
        if 'key pressed: ' in line:
            action_id = int(line[line.index('[') + 1: line.index(']')].replace(' ', ''))
            if abs(action_id - self.last_action_id) < 5:
                return

            self.last_action_id = action_id
            index_start = line.index('key pressed: ') + 13
            index_end = line.index(' (', index_start)
            key = line[index_start: index_end].lower()
            Logger().write(LogVerbosity.Debug, "CEC key press: " + key)
            callbacks = [x.callback for x in self.key_callbacks if x.key == key]
            for callback in callbacks:
                callback(key)

    def start(self):
        if not self.pi:
            return

        self.cec_process = subprocess.Popen(['cec-client'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t = CustomThread(self.__read_cec, "Cec reader", [])
        t.start()

    @staticmethod
    def __construct_request(source, destination, command):
        return 'echo "tx ' + source + destination + ":" + command + '" | cec-client -s'

    def __request(self, command):
        Logger().write(LogVerbosity.Debug, "TV manager sending command: " + command)
        result = subprocess.check_output('echo "' + command + '" | cec-client -s -d ' + self.debug_level, shell=True).decode("utf8")
        Logger().write(LogVerbosity.Debug, "TV manager result: " + str(result))


class KeyCallback:

    def __init__(self, key, callback):
        self.key = key
        self.callback = callback
