import subprocess

from Shared.Logger import Logger
from Shared.Util import Singleton
from WebServer.Models import CecDevice


class TVManager(metaclass=Singleton):

    # 0 - TV
    # 1,2 - Recording 1/2
    # 3,6,7,A - Tuner 1/2/3/4
    # 4,8,B - Playback 1/2/3

    pi_source = "1"
    tv_source = "0"
    decoder_source = "2" #??
    debug_level = "1"

    key_map = {
        "channel_up": 30,
        "channel_down": 31,
        "0": 20,
        "1": 21,
        "2": 22,
        "3": 23,
        "4": 24,
        "5": 25,
        "6": 26,
        "7": 27,
        "8": 28,
        "9": 29,
     }

    def __init__(self):
        pass

    def channel_up(self):
        return self.__send_key(TVManager.key_map['channel_up'])

    def channel_down(self):
        return self.__send_key(TVManager.key_map['channel_down'])

    def channel_number(self, number):
        return self.__send_key(TVManager.key_map[str(number)])

    def __send_key(self, key):
        return self.__request(self.__construct_request(TVManager.pi_source, TVManager.decoder_source, '44:'+str(key)))

    def switch_input_to_pi(self):
        return self.__request(self.__construct_request(TVManager.pi_source, TVManager.tv_source, '82:' + TVManager.pi_source + '0:00'))

    def switch_input_to_tv(self):
        return self.__request(self.__construct_request(TVManager.pi_source, TVManager.tv_source, '82:' + TVManager.decoder_source + '0:00'))

    def turn_tv_on(self):
        return self.__request('echo "on ' + TVManager.tv_source + '" | cec-client -s')

    def turn_tv_off(self):
        return self.__request(self.__construct_request(TVManager.pi_source, TVManager.tv_source, "36"))

    def get_inputs(self):
        data = self.__request('echo "scan" | cec-client RPI -s')
        if not data:
            return []

        return self.__process_devices(data)

    def __construct_request(self, source, destination, command):
        return 'echo "tx ' + source + destination + ":" + command + '" | cec-client -s'

    def __process_devices(self, data):
        result = []
        lines = data.split('\n')
        current_device = None
        for line in lines:
            if line.startswith("device #"):
                # new device
                current_device = CecDevice()

            if line.startswith("address: "):
                current_device.address = line.split(" ")[-1]
            if line.startswith("active source: "):
                current_device.active = line.split(" ")[-1] == "yes"
            if line.startswith("vendor: "):
                current_device.vendor = line.split(" ")[-1]
            if line.startswith("osd string: "):
                current_device.osd = line.split(" ")[-1]
            if not line:
                if current_device:
                    result.append(current_device)
                    current_device = None

        return result

    def __request(self, command):
        try:
            Logger.write(2, "TV manager sending command: " + command)
            result = subprocess.check_output(command + ' -d ' + TVManager.debug_level)
            Logger.write(2, "TV manager result: " + result)
            return result
        except subprocess.TimeoutExpired:
            Logger.write(2, "TV manager request failed by timeout")
        except subprocess.CalledProcessError as err:
            Logger.write(2, "TV manager request failed: {}".format(err))
