import threading
from enum import Enum
from threading import Lock

from Shared.Logger import Logger


class EventType(Enum):
    InitialSeeking = 1,
    ProcessSeeking = 26
    IMDbKnown = 2,
    StreamFileHashKnown = 3,

    StartPlayer = 4,
    PlayerStarted = 5
    PlayerOpening = 18,
    PlayerBuffering = 19,
    PlayerNothingSpecial = 20,
    PlayerBufferingDone = 21,
    StopPlayer = 6,
    PlayerStopped = 7
    SetVolume = 8,
    PauseResumePlayer = 9,
    PlayerPaused = 10,
    PlayerError = 11,

    SetSubtitleFile = 12,
    SetSubtitleId = 13,
    SetSubtitleOffset = 14,

    SetAudioId = 24,

    StopTorrent = 15,
    StartTorrent = 16,
    InvalidTorrent = 22,

    Error = 17,

    NewDHTNode = 23,
    RequestDHTPeers = 25,
    PlayerStateChange = 27,
    Log = 28,
    StreamTorrentStarted = 29,
    StreamTorrentStopped = 30,
    StopStreamTorrent = 31


class EventManager:

    last_registered_id = 0
    registered_events = []
    lock = Lock()

    @staticmethod
    def throw_event(event_type, args):
        thread = threading.Thread(target=EventManager.execute_handlers, args=[event_type, args])
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
