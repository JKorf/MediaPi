import json
import time
from enum import Enum

from Shared.Logger import Logger


def current_time():
    return int(round(time.time() * 1000))


def to_JSON(obj):
    return json.dumps(obj, default=default_serializer,
                      sort_keys=True, indent=4)


def default_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, Enum):
        serial = obj.value
        return serial

    return {x: obj.__dict__[x] for x in obj.__dict__ if not x.startswith("_")}


def write_size(data):
    if data < 1100:
        return str(data) + 'kb'
    if data < 1100000:
        return str(round(data / 1000, 2)) + 'kb'
    if data < 1100000000:
        return str(round(data / 1000000, 2)) + 'mb'
    if data < 1100000000000:
        return str(round(data / 1000000000, 2)) + 'gb'
    else:
        return str(round(data / 1000000000, 2)) + 'tb'


def write_time_from_seconds(t):
    return time.strftime('%H:%M:%S', time.gmtime(t))


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            Logger.write(1, "Creating singleton: " + str(cls))
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}
