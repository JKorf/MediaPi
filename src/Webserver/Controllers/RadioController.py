import time

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Util import to_JSON
from Webserver.Providers.RadioProvider import RadioProvider


class RadioController:

    @staticmethod
    def get_radios():
        Logger.write(2, "Get radio list")
        return to_JSON(RadioProvider.get_list())

    @staticmethod
    def play_radio(id):
        Logger.write(2, "Play radio: " + id)
        radio = RadioProvider.get_by_id(int(id))
        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(0.2)
        EventManager.throw_event(EventType.PreparePlayer, ["Radio", radio.name, radio.url, radio.image, 0, None])
        EventManager.throw_event(EventType.StartPlayer, [])
