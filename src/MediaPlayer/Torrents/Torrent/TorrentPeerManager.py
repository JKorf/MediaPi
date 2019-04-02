from random import Random
from urllib.parse import urlparse

from pympler import asizeof

from MediaPlayer.Torrents.Peer.PeerMessages import HaveMessage

from MediaPlayer.Torrents.Peer.Peer import Peer
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

    def unregister(self):
        EventManager.deregister_event(self._event_id_stopped)
        EventManager.deregister_event(self._event_id_torrent_change)
        EventManager.deregister_event(self._event_id_peers_found)

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

    def piece_done(self, piece):
        Logger().write(LogVerbosity.Debug, "Sending have messages for piece " + str(piece.index))
        for peer in list(self.connected_peers):
            peer.protocol_logger.update("Sending Have", True)
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

    def should_stop_peers(self):
        if self.torrent.state != TorrentState.Downloading and self.torrent.state != TorrentState.DownloadingMetaData:
            return False

        if current_time() - self.download_start < 20000:
            return False

        if self.torrent.network_manager.throttling:
            return False

        if len(self.potential_peers) < self.max_peers_connected - len(self.connected_peers):
            return False

        return True

    def stop_slowest_peer(self):
        if not self.should_stop_peers():
            return True

        if self.max_peers_connected - len(self.connected_peers) > 3:
            return True  # No need to stop slowest if we have enough room to connect more

        peers_to_check = [x for x in self.connected_peers if current_time() - x.connection_manager.connected_on > 30000]
        peers_to_check = sorted(peers_to_check, key=lambda x: x.counter.value)
        if len(peers_to_check) == 0:
            return True

        slowest = peers_to_check[0]
        if slowest.counter.value > 100000:  # if the slowest peer is downloading with more than 100kbps we're fine
            return True

        Logger().write(LogVerbosity.Info, str(slowest.id) + " stopping peer to find a potential faster one. Peer speed last 5 seconds was " + str(write_size(slowest.counter.value)) + ", total: " + str(write_size(slowest.counter.total)))
        slowest.stop_async("Slowest")
        return True

    def get_peers_for_reading(self):
        return sorted([x for x in self.connected_peers if x.connection_manager.ready_for_reading], key=lambda p: p.connection_manager._last_communication)

    def get_peers_for_writing(self):
        return [x for x in self.connected_peers if x.connection_manager.ready_for_sending]

    def are_fast_peers_available(self):
        return self.high_speed_peers > 0 or self.medium_speed_peers > 1

    def stop(self):
        for peer in self.connecting_peers:
            peer.stop_async("Stopping torrent")

        for peer in self.connected_peers:
            peer.stop_async("Stopping torrent")

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
