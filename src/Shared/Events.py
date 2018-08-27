import threading
from enum import Enum
from threading import Lock

from Shared.Logger import Logger


class EventType(Enum):
    HashDataKnown = 1,

    Seek = 2,
    StartPlayer = 3,
    PreparePlayer = 35,
    StopPlayer = 9,
    PlayerStopped = 10
    SetVolume = 11,
    PauseResumePlayer = 12,
    PlayerPaused = 13,
    PlayerError = 14,
    PlayerStateChange = 15,

    SetSubtitleFile = 16,
    SetSubtitleId = 17,
    SetSubtitleOffset = 18,
    SubtitleDownloaded = 19,

    SetAudioId = 22,

    StartTorrent = 23,
    StopTorrent = 24,
    TorrentMetadataDone = 25
    TorrentStopped = 26
    TorrentMediaFileSet = 34

    Error = 27,

    NewDHTNode = 28,
    RequestDHTPeers = 29,
    Log = 30,

    NewRequest = 31,
    TorrentMediaSelectionRequired = 32
    TorrentMediaFileSelection = 33
    NextEpisodeSelection = 36,
    SetNextEpisode = 37


class EventManager:

    last_registered_id = 0
    registered_events = []
    lock = Lock()

    @staticmethod
    def throw_event(event_type, args):
        thread = threading.Thread(name="Evnt " + str(event_type), target=EventManager.execute_handlers, args=[event_type, args])
        thread.daemon = True
        thread.start()

    @staticmethod
    def execute_handlers(event_type, args):
        Logger.write(1, "Firing event " + str(event_type))
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
