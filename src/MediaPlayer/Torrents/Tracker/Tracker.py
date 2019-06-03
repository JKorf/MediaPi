import random
import time
from urllib.parse import urlparse

from MediaPlayer.Torrents.Tracker import TrackerMessages
from MediaPlayer.Util import Bencode
from MediaPlayer.Util.Bencode import BTFailure
from MediaPlayer.Util.Enums import PeerSource
from MediaPlayer.Util.Util import uri_from_bytes
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory, UdpClient
from Shared.Settings import Settings
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
        self.last_announce = 0
        self.tracker_peer_request_amount = Settings.get_int("tracker_peer_request_amount")

    def announce_torrent(self, torrent):
        self.last_announce = current_time()
        announce_message = TrackerMessages.TrackerAnnounceMessage.for_http(torrent.info_hash, 2, torrent.total_size - torrent.left, torrent.left, torrent.uploaded, self.tracker_peer_request_amount)

        path = self.uri.path + announce_message.as_param_string()
        response = RequestFactory.make_request(path)
        if response is None:
            return False

        try:
            response_dict = Bencode.bdecode(response)
        except BTFailure:
            Logger().write(LogVerbosity.Info, 'Invalid tracker response: ' + str(response))
            return False

        if b"peers" not in response_dict:
            return False

        peers_data = response_dict[b"peers"]
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
        self.last_announce = 0
        self.transaction_id = 0
        self.connection_id = 0
        self.connection_id_retrieved = 0
        self.connection = UdpClient(host, port, Settings.get_int("connection_timeout") / 1000)
        self.tracker_peer_request_amount = Settings.get_int("tracker_peer_request_amount")

    def connect(self):
        if self.connection_id_retrieved > current_time() - (1000 * 60):
            # If we already have a connection id which is still valid ( 1 minute ), use this one
            return True

        self.transaction_id = random.randint(0, 9999999)
        self.connection_id = 0x41727101980

        connection_message = TrackerMessages.TrackerConnectionMessage(self.connection_id, self.transaction_id, 0)
        send_okay = self.connection.send(connection_message.as_bytes())
        data = self.connection.receive()
        if not send_okay or data is None:
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
                                                                          torrent.total_size - torrent.left, torrent.left, torrent.uploaded, self.tracker_peer_request_amount,
                                                                          6881)

        send_okay = self.connection.send(announce_message.as_bytes())
        response_message_bytes = self.connection.receive()
        if not send_okay or response_message_bytes is None:
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

        self.request_peers_id = EventManager.register_event(EventType.RequestPeers, self.request_peers)

    def request_peers(self, torrent):
        if not self.initialized:
            for uri in torrent.announce_uris:
                if len([x for x in self.trackers if x.host == uri]) == 0:
                    tracker = TrackerFactory.create_tracker(uri)
                    if tracker is not None:
                        self.trackers.append(tracker)
            Logger().write(LogVerbosity.Debug, "Initialized " + str(len(self.trackers)) + " trackers")
            self.initialized = True

        for tracker in self.trackers:
            thread = CustomThread(self.tracker_announce, "Tracker announce", [tracker, torrent])
            thread.start()

    @staticmethod
    def tracker_announce(tracker, torrent):
        if not tracker.announce_torrent(torrent):
            Logger().write(LogVerbosity.Debug, 'Could not connect to tracker: ' + tracker.host)
        else:
            Logger().write(LogVerbosity.Debug, 'Tracker ok: ' + tracker.host)

    def stop(self):
        EventManager.deregister_event(self.request_peers_id)
