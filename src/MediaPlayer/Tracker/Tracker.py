import random
import time
from urllib.parse import urlparse

from MediaPlayer.Connections import HttpClient, UdpClient
from MediaPlayer.Tracker import TrackerMessages
from MediaPlayer.Util import Bencode
from MediaPlayer.Util.Bencode import BTFailure
from MediaPlayer.Util.Enums import PeerSource
from MediaPlayer.Util.Util import uri_from_bytes
from Shared.Events import EventManager, EventType
from Shared.Logger import *
from Shared.Threading import CustomThread
from Shared.Util import current_time


class TrackerFactory:

    @staticmethod
    def create_tracker(uri):
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme == 'udp':
            return UdpTracker(parsed_uri.hostname, parsed_uri.port if parsed_uri.port is not None else 80)
        elif parsed_uri.scheme == 'http':
            return HttpTracker(parsed_uri)


class HttpTracker:

    def __init__(self, uri):
        self.uri = uri
        self.host = uri.hostname
        self.could_connect = True
        self.try_number = 0
        self.last_announce = 0
        self.connection = HttpClient()
        self.tracker_peer_request_amount = Settings.get_int("tracker_peer_request_amount")

    def announce_torrent(self, torrent):
        self.last_announce = current_time()
        announce_message = TrackerMessages.TrackerAnnounceMessage.for_http(torrent.info_hash, 2, torrent.download_counter.total, torrent.left, torrent.uploaded, self.tracker_peer_request_amount)

        path = self.uri.path + announce_message.as_param_string()
        response = self.connection.send_receive(self.uri.scheme + "://" + self.uri.netloc, path)
        if response is None:
            return False

        try:
            dict = Bencode.bdecode(response)
        except BTFailure:
            Logger.write(2, 'Invalid tracker response: ' + str(response))
            return False

        if b"peers" not in dict:
            return False

        peers_data = dict[b"peers"]
        total_peers = int(len(peers_data) / 6)
        offset = 0
        peers = []
        for index in range(total_peers):
            peers.append(uri_from_bytes(peers_data[offset:offset + 6]))
            offset += 6
        EventManager.throw_event(EventType.PeersFound, [peers, PeerSource.HttpTracker])


class UdpTracker:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.could_connect = True
        self.last_announce = 0
        self.transaction_id = 0
        self.connection_id = 0
        self.connection_id_retrieved = 0
        self.try_number = 0
        self.connection = UdpClient(host, port)
        self.tracker_peer_request_amount = Settings.get_int("tracker_peer_request_amount")

    def connect(self):
        if self.connection_id_retrieved > current_time() - (1000 * 60):
            # If we already have a connection id which is still valid ( 1 minute ), use this one
            return True

        self.transaction_id = random.randint(0, 9999999)
        self.connection_id = 0x41727101980

        connection_message = TrackerMessages.TrackerConnectionMessage(self.connection_id, self.transaction_id, 0)
        data = self.connection.send_receive(connection_message.as_bytes())
        if data is None:
            return False

        response_message = TrackerMessages.TrackerConnectionMessage.for_receive(data)
        if response_message is None:
            return False

        self.connection_id = response_message.connection_id
        self.connection_id_retrieved = current_time()
        return True

    def announce_torrent(self, torrent):
        self.last_announce = current_time()

        if not self.connect():
            return False

        announce_message = TrackerMessages.TrackerAnnounceMessage.for_udp(self.connection_id, self.transaction_id, torrent.info_hash, 2,
                                                                          torrent.download_counter.total, torrent.left, torrent.uploaded, self.tracker_peer_request_amount,
                                                                          6881)

        response_message_bytes = self.connection.send_receive(announce_message.as_bytes())
        if response_message_bytes is None:
            return False

        response_message = TrackerMessages.TrackerResponseMessage.from_bytes(response_message_bytes)
        if response_message is None or response_message.error is not None:
            return False

        EventManager.throw_event(EventType.PeersFound, [response_message.peers, PeerSource.UdpTracker])
        return True


class TrackerManager:

    def __init__(self):
        self.trackers = []
        self.initialized = False
        self.running = True

        self.tracker_retry = Settings.get_int("tracker_retry")
        self.request_peers_id = EventManager.register_event(EventType.RequestPeers, self.request_peers)

    def request_peers(self, torrent):
        for uri in torrent.announce_uris:
            if len([x for x in self.trackers if x.host == uri]) == 0:
                tracker = TrackerFactory.create_tracker(uri)
                if tracker is not None:
                    self.trackers.append(tracker)

        for tracker in self.trackers:
            if tracker.could_connect:
                thread = CustomThread(self.tracker_announce, "Tracker announce", [tracker, torrent])
                thread.start()

    def tracker_announce(self, tracker, torrent):
        if not tracker.announce_torrent(torrent):
            if tracker.try_number > self.tracker_retry:
                return

            tracker.could_connect = False
            Logger.write(1, 'Could not connect to tracker ' + tracker.host)
            self.sleep(15 * 2 ^ tracker.try_number)
            if not self.running:
                return
            tracker.try_number += 1
            self.tracker_announce(tracker, torrent)
        else:
            tracker.try_number = 0
            tracker.could_connect = True
            Logger.write(1, 'Tracker ok! ' + tracker.host)

    def sleep(self, t):
        slept = 0
        while slept < t:
            time.sleep(1)
            slept += 1
            if not self.running:
                return

    def stop(self):
        self.running = False
        EventManager.deregister_event(self.request_peers_id)