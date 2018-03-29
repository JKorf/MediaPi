import random
import time
from urllib.parse import urlparse

from Shared.Events import EventManager, EventType
from TorrentSrc.Util import Bencode
from TorrentSrc.Util.Bencode import BTFailure

from Shared.Logger import *
from Shared.Util import current_time
from TorrentSrc.Connections import *
from TorrentSrc.Tracker import TrackerMessages
from TorrentSrc.Util.Threading import CustomThread
from TorrentSrc.Util.Util import uri_from_bytes
from TorrentSrc.Util.Enums import PeerSource


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

        peers = dict[b"peers"]
        total_peers = int(len(peers) / 6)
        offset = 0
        for index in range(total_peers):
            torrent.peer_manager.add_potential_peers(uri_from_bytes(peers[offset:offset + 6]), PeerSource.HttpTracker)
            offset += 6


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
        self.initial = True
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

        torrent.available_leechers = response_message.leechers
        torrent.available_seeders = response_message.seeders
        torrent.peer_manager.add_potential_peers(response_message.peers, PeerSource.UdpTracker)
        return True


class TrackerManager:

    def __init__(self, torrent):
        self.torrent = torrent
        self.trackers = []
        self.initialized = False
        self.running = True
        self.peer_request_interval = Settings.get_int("peer_request_interval")
        self.peer_request_interval_no_potential = Settings.get_int("peer_request_interval_no_potential")
        self.tracker_retry = Settings.get_int("tracker_retry")
        self.dht_request_interval = Settings.get_int("dht_request_interval")
        self.last_dht_get = 0

    def update(self):
        if not self.initialized:
            self.initialized = True
            for uri in self.torrent.announce_uris:
                tracker = TrackerFactory.create_tracker(uri)
                if tracker is not None:
                    self.trackers.append(tracker)

            for uri in ExtraTrackerList.load():
                tracker = TrackerFactory.create_tracker(uri)
                if tracker is not None:
                    self.trackers.append(tracker)

        if len(self.torrent.peer_manager.potential_peers) > 1000:
            return True

        for tracker in self.trackers:
            if tracker.could_connect:
                if (current_time() - tracker.last_announce > self.peer_request_interval) or \
                        (len(self.torrent.peer_manager.potential_peers) < 10 and current_time() - tracker.last_announce > self.peer_request_interval_no_potential):
                    thread = CustomThread(self.tracker_announce, "Tracker announce", [tracker])
                    thread.start()

        if current_time() - self.last_dht_get > self.dht_request_interval:
            self.last_dht_get = current_time()
            EventManager.throw_event(EventType.RequestDHTPeers, [self.torrent])

        return True

    def tracker_announce(self, tracker):
        if not tracker.announce_torrent(self.torrent):
            if tracker.try_number > self.tracker_retry:
                return

            tracker.could_connect = False
            Logger.write(1, 'Could not connect to tracker ' + tracker.host)
            self.sleep(15 * 2 ^ tracker.try_number)
            if not self.running:
                return
            tracker.try_number += 1
            self.tracker_announce(tracker)
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


class ExtraTrackerList:

    @staticmethod
    def load():
        result = []

        if not Settings.get_bool("use_external_trackers"):
            return result

        filepath = os.getcwd() + "\\trackers.txt"
        if not os.path.isfile(filepath):
            Logger.write(2, 'External trackers enabled, but no trackers file found')
            return result

        with open(filepath) as f:
            for line in f:
                line = line.replace("\r", "").replace("\n", "")
                if line.startswith('udp://') or line.startswith('http://'):
                    result.append(line)

        Logger.write(2, "Added " + str(len(result)) + " external trackers")
        return result

