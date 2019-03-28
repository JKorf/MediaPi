from random import Random
from urllib.parse import urlparse

from pympler import asizeof

from MediaPlayer.TorrentStreaming.Peer.PeerMessages import HaveMessage

from MediaPlayer.TorrentStreaming.Peer.Peer import Peer
from MediaPlayer.Util.Enums import PeerSource, TorrentState, PeerSpeed, PeerState
from Shared.Events import EventManager, EventType
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Util import current_time, write_size


class TorrentPeerManager(LogObject):
    __peer_id = 0

    def __init__(self, torrent):
        super().__init__(torrent, "peers")

        self.torrent = torrent
        self.potential_peers = []
        self.connecting_peers = []
        self.connected_peers = []
        self.disconnected_peers = []
        self.cant_connect_peers = []
        self.complete_peer_list = []
        self.max_peers_connected = Settings.get_int("max_peers_connected")
        self.max_peers_connecting = Settings.get_int("max_peers_connecting")
        self._peer_request_interval = Settings.get_int("peer_request_interval")
        self._peer_request_interval_no_potential = Settings.get_int("peer_request_interval_no_potential")
        self.random = Random()
        self.download_start = 0
        self.start_time = current_time()
        self.last_peer_request = 0
        self.checked_no_peers = False

        self._event_id_log = EventManager.register_event(EventType.Log, self.log_peers)
        self._event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)
        self._event_id_torrent_change = EventManager.register_event(EventType.TorrentStateChange, self.torrent_state_change)
        self._event_id_peers_found = EventManager.register_event(EventType.PeersFound, self.add_potential_peers)

        self.high_speed_peers = 0
        self.medium_speed_peers = 0

        # Log properties
        self.potential_peers_log = 0
        self.connecting_peers_log = 0
        self.connected_peers_log = 0
        self.disconnected_peers_log = 0
        self.cant_connect_peers_log = 0

    def check_size(self):
        for key, size in sorted([(key, asizeof.asizeof(value)) for key, value in self.__dict__.items()], key=lambda key_value: key_value[1], reverse=True):
            Logger().write(LogVerbosity.Important, "       Size of " + str(key) + ": " + write_size(size))

    def unregister(self):
        EventManager.deregister_event(self._event_id_log)
        EventManager.deregister_event(self._event_id_stopped)
        EventManager.deregister_event(self._event_id_torrent_change)
        EventManager.deregister_event(self._event_id_peers_found)

    def log_peers(self):
        Logger().write(LogVerbosity.Important, "-- TorrentPeerManager state --")
        Logger().write(LogVerbosity.Important, "   Potential peers: " + str(len(self.potential_peers)))
        Logger().write(LogVerbosity.Important, "   Connected peers: " + str(len(self.connected_peers)))
        Logger().write(LogVerbosity.Important, "   Connecting peers: " + str(len(self.connecting_peers)))
        Logger().write(LogVerbosity.Important, "   CantConnect peers: " + str(len(self.cant_connect_peers)))
        Logger().write(LogVerbosity.Important, "   Disconnected peers: " + str(len(self.disconnected_peers)))
        Logger().write(LogVerbosity.Important, "   Complete list: " + str(len(self.complete_peer_list)))
        for peer in self.connected_peers:
            peer.log()

    def torrent_state_change(self, old_state, new_state):
        if new_state == TorrentState.Downloading:
            self.download_start = current_time()

    def add_potential_peers(self, uri, source):
        if len(self.potential_peers) > 1000:
            return

        if isinstance(uri, list):
            Logger().write(LogVerbosity.Debug, "Adding " + str(len(uri)) + " potential peers from " + str(source))
            for u in uri:
                self.add_potential_peer_item(u, source)
        else:
            Logger().write(LogVerbosity.Debug, "Adding a potential peers from " + str(source))
            self.add_potential_peer_item(uri, source)
        self.potential_peers_log = len(self.potential_peers)

    def add_potential_peer_item(self, uri, source):
        if uri not in self.complete_peer_list:
            self.complete_peer_list.append(uri)
            self.potential_peers.append((urlparse(uri), source))
            self.add_potential_peer_stat(source)

    @staticmethod
    def add_potential_peer_stat(source):
        if source == PeerSource.DHT:
            Stats.add('peers_source_dht', 1)
        elif source == PeerSource.HttpTracker:
            Stats.add('peers_source_http_tracker', 1)
        elif source == PeerSource.UdpTracker:
            Stats.add('peers_source_udp_tracker', 1)
        elif source == PeerSource.PeerExchange:
            Stats.add('peers_source_exchange', 1)

    def pieces_done(self, pieces):
        for piece in pieces:
            Logger().write(LogVerbosity.Debug, "Sending have messages for piece " + str(piece.index))
            for peer in list(self.connected_peers):
                peer.connection_manager.send(HaveMessage(piece.index).to_bytes())

    def update_new_peers(self):
        if self.torrent.state != TorrentState.Downloading and self.torrent.state != TorrentState.DownloadingMetaData and self.torrent.state != TorrentState.WaitingUserFileSelection:
            return True

        if self.torrent.network_manager.throttling:
            return True  # currently throttling, no need to request more peers

        if current_time() - self.last_peer_request > self._peer_request_interval or \
                                len(self.potential_peers) <= 10 and current_time() - self.last_peer_request > self._peer_request_interval_no_potential:
            Logger().write(LogVerbosity.Debug, "Requesting peers")
            EventManager.throw_event(EventType.RequestPeers, [self.torrent])
            self.last_peer_request = current_time()

        currently_connecting = len(self.connecting_peers)
        currently_connected = len(self.connected_peers)

        if not self.checked_no_peers and current_time() - self.start_time > 45000:
            self.checked_no_peers = True

            if len(self.potential_peers) == 0 and currently_connecting == 0 and currently_connected == 0:
                Logger().write(LogVerbosity.Important, "No peers found for torrent, stopping")
                EventManager.throw_event(EventType.NoPeers, [])
                return False

        if currently_connected >= self.max_peers_connected:
            # already have max connections
            return True

        if currently_connecting >= self.max_peers_connecting:
            # already have max connecting
            return True

        connected_peers_under_max = self.max_peers_connected - currently_connected
        connecting_peers_under_max = self.max_peers_connecting - currently_connecting
        peers_to_connect = min(connecting_peers_under_max, connected_peers_under_max)

        peer_list = self.potential_peers  # Try connecting to new peers from potential list
        peer_list_size = len(peer_list)
        using_disconnected = False
        if peer_list_size == 0:
            using_disconnected = True
            peer_list = [x for x in self.disconnected_peers if current_time() - x[2] > 10000][peers_to_connect:]  # If we dont have any new peers to try, try connecting to disconnected peers
            peer_list_size = len(peer_list)
            if peer_list_size == 0:
                return True  # No peers available

        peers_to_connect = min(peer_list_size, peers_to_connect)
        Logger().write(LogVerbosity.Debug, 'starting ' + str(peers_to_connect) + ' new peers')
        selected_peers = self.random.sample(peer_list, peers_to_connect)
        if not using_disconnected:
            self.potential_peers = [x for x in peer_list if x not in selected_peers]
        else:
            self.disconnected_peers = [x for x in peer_list if x not in selected_peers]
        for peer in selected_peers:
            self.__peer_id += 1
            new_peer = Peer(self.__peer_id, self.torrent, peer[0], peer[1])
            new_peer.start()

        self.potential_peers_log = len(self.potential_peers)
        self.disconnected_peers_log = len(self.disconnected_peers)
        return True

    def update_peer(self, peer, from_state, to_state):
        if from_state == PeerState.Initial and to_state == PeerState.Starting:
            self.connecting_peers.append(peer)
        elif from_state == PeerState.Starting and to_state == PeerState.Started:
            self.connecting_peers.remove(peer)
            self.connected_peers.append(peer)
        elif from_state == PeerState.Starting and to_state == PeerState.Stopping:
            self.connecting_peers.remove(peer)
            self.cant_connect_peers.append(peer)
        elif from_state == PeerState.Started and to_state == PeerState.Stopping:
            self.connected_peers.remove(peer)
            self.disconnected_peers.append((peer.uri, peer.source, current_time(), peer.counter.total))

        self.high_speed_peers = len([x for x in self.connected_peers if x.peer_speed == PeerSpeed.High])
        self.medium_speed_peers = len([x for x in self.connected_peers if x.peer_speed == PeerSpeed.Medium])
        self.connected_peers = sorted(self.connected_peers, key=lambda x: x.counter.value, reverse=True)
        self.disconnected_peers = sorted(self.disconnected_peers, key=lambda x: x[3], reverse=True)

        self.connecting_peers_log = len(self.connecting_peers)
        self.connected_peers_log = len(self.connected_peers)
        self.cant_connect_peers_log = len(self.cant_connect_peers)
        self.disconnected_peers_log = len(self.disconnected_peers)

    def update_bad_peers(self):
        if self.torrent.state != TorrentState.Downloading and self.torrent.state != TorrentState.DownloadingMetaData:
            return True

        if self.torrent.network_manager.throttling:
            return True  # currently throttling, don't stop slow peers because they might just be throttled

        if len(self.connected_peers) < self.max_peers_connected ** 0.66:
            return True  # Don't stop any peers if we have less than 66% of the max amount of peers

        if current_time() - self.download_start < 20000:
            return True  # Don't drop peers if we only recently started downloading again

        if len(self.potential_peers) < self.max_peers_connected - len(self.connected_peers):
            return True  # Don't stop peers if we don't have enough new

        peers_to_check = [x for x in self.connected_peers if current_time() - x.connection_manager.connected_on > 30000]
        peers_to_check = sorted(peers_to_check, key=lambda x: x.counter.total)
        for peer in peers_to_check:
            if peer.counter.value > 5000:
                # If peer speed is more than 5kbps don't remove
                break

            Logger().write(LogVerbosity.Info, "Stopping slowest peer to find a potential faster one. Peer speed last 5 seconds was " + str(write_size(peer.counter.value)) + ", total: " + str(write_size(peer.counter.total)))
            peer.stop_async()

        return True

    def get_peers_for_io(self):
        return sorted(self.connected_peers, key=lambda p: p.connection_manager._last_communication), [x for x in self.connected_peers if len(x.connection_manager.to_send_bytes) > 0]

    def are_fast_peers_available(self):
        return self.high_speed_peers > 0 or self.medium_speed_peers > 1

    def stop(self):
        for peer in self.connecting_peers:
            peer.stop_async()

        for peer in self.connected_peers:
            peer.stop_async()

        self.complete_peer_list.clear()
        self.potential_peers.clear()
        self.cant_connect_peers.clear()
        self.disconnected_peers.clear()

        self.potential_peers_log = 0
        self.connecting_peers_log = 0
        self.connected_peers_log = 0
        self.cant_connect_peers_log = 0
        self.disconnected_peers_log = 0

        self.torrent = None
