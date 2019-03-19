from enum import Enum
from threading import Lock

from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread


class EventType(Enum):
    SearchSubtitles = 1
    Seek = 2
    StopPlayer = 9
    SetSubtitleFiles = 16
    TorrentStopped = 26
    TorrentMediaFileSet = 34
    TorrentStateChange = 37
    Error = 27
    NewDHTNode = 28
    Log = 30
    TorrentMediaSelectionRequired = 32
    TorrentMediaFileSelection = 33
    NoPeers = 38
    PeersFound = 40
    RequestPeers = 41


class EventManager:

    last_registered_id = 0
    registered_events = []
    lock = Lock()

    @staticmethod
    def throw_event(event_type, args):
        thread = CustomThread(EventManager.execute_handlers, "EventHandler " + str(event_type), args=[event_type, args])
        thread.start()

    @staticmethod
    def execute_handlers(event_type, args):
        Logger().write(LogVerbosity.All, "Firing event " + str(event_type))
        with EventManager.lock:
            to_handle = [x for x in EventManager.registered_events if x[1] == event_type]

        for id, event_type, handler in to_handle:
            handler(*args)

    @staticmethod
    def register_event(event_type, callback):
        with EventManager.lock:
            EventManager.last_registered_id += 1
            EventManager.registered_events.append((EventManager.last_registered_id, event_type, callback))
        return EventManager.last_registered_id

    @staticmethod
    def deregister_event(id):
        with EventManager.lock:
            EventManager.registered_events = [x for x in EventManager.registered_events if x[0] != id]
