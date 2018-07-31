import threading
from enum import Enum
from threading import Lock

from Shared.Logger import Logger


class EventType(Enum):
    HashDataKnown = 1,

    Seek = 2,
    StartPlayer = 3,
    PlayerStarted = 4
    PlayerOpening = 5,
    PlayerBuffering = 6,
    PlayerNothingSpecial = 7,
    PlayerBufferingDone = 8,
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
    SubsDoneChange = 20,
    SearchAdditionalSubs = 21,

    SetAudioId = 22,

    StartTorrent = 23,
    StopTorrent = 24,
    TorrentMetadataDone = 25
    TorrentStopped = 26

    Error = 27,

    NewDHTNode = 28,
    RequestDHTPeers = 29,
    Log = 30,

    NewRequest = 31,
    TorrentMediaSelectionRequired = 32
    TorrentMediaFileSelection = 33


class EventManager:

    last_registered_id = 0
    registered_events = []
    lock = Lock()

    @staticmethod
    def throw_event(event_type, args):
        thread = threading.Thread(name="EventHandler " + str(event_type), target=EventManager.execute_handlers, args=[event_type, args])
        thread.daemon = True
        thread.start()

    @staticmethod
    def execute_handlers(event_type, args):
        Logger.write(1, "Firing event " + str(event_type))
        EventManager.lock.acquire()
        to_handle = [x for x in EventManager.registered_events if x[1] == event_type]
        EventManager.lock.release()

        for id, event_type, handler in to_handle:
            Logger.write(1, "Firing event on id " + str(id) + ", event type = " + str(event_type))
            handler(*args)

    @staticmethod
    def register_event(event_type, callback):
        EventManager.lock.acquire()
        EventManager.last_registered_id += 1
        EventManager.registered_events.append((EventManager.last_registered_id, event_type, callback))
        EventManager.lock.release()
        Logger.write(1, "Registered event with id " + str(EventManager.last_registered_id) + " for event " + str(event_type))
        return EventManager.last_registered_id

    @staticmethod
    def deregister_event(id):
        Logger.write(1, "Deregistered event with id " + str(id))
        EventManager.lock.acquire()
        EventManager.registered_events = [x for x in EventManager.registered_events if x[0] != id]
        EventManager.lock.release()
