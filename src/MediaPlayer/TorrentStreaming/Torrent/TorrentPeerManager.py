from random import Random
from urllib.parse import urlparse

from MediaPlayer.TorrentStreaming.Peer.PeerMessages import HaveMessage

from MediaPlayer.TorrentStreaming.Peer.Peer import Peer
from MediaPlayer.Util.Enums import PeerSource, TorrentState, ConnectionState, PeerSpeed
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Util import current_time, write_size


class TorrentPeerManager:
    __peer_id = 0

    def __init__(self, torrent):
        self.torrent = torrent
        self.potential_peers = []
        self.connecting_peers = []
        self.connected_peers = []
        self.disconnected_peers = []
        self.cant_connect_peers = []
        self.complete_peer_list = []
        self.max_peers_connected = Settings.get_int("max_peers_connected")
        self.max_peers_connecting = Settings.get_int("max_peers_connecting")
        self.peer_request_interval = Settings.get_int("peer_request_interval")
        self.peer_request_interval_no_potential = Settings.get_int("peer_request_interval_no_potential")
        self.random = Random()
        self.download_start = 0
        self.start_time = current_time()
        self.last_peer_request = 0
        self.checked_no_peers = False

        self.event_id_log = EventManager.register_event(EventType.Log, self.log_peers)
        self.event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)
        self.event_id_torrent_change = EventManager.register_event(EventType.TorrentStateChange, self.torrent_state_change)
        self.event_id_peers_found = EventManager.register_event(EventType.PeersFound, self.add_potential_peers)

        self.high_speed_peers = 0
        self.medium_speed_peers = 0

    def unregister(self):
        EventManager.deregister_event(self.event_id_log)
        EventManager.deregister_event(self.event_id_stopped)
        EventManager.deregister_event(self.event_id_torrent_change)
        EventManager.deregister_event(self.event_id_peers_found)

    def log_peers(self):
        with Logger.lock:
            Logger.write(3, "-- TorrentPeerManager state --")
            Logger.write(3, "   Potential peers: " + str(len(self.potential_peers)))
            Logger.write(3, "   Connected peers: " + str(len(self.connected_peers)))
            Logger.write(3, "   Connecting peers: " + str(len(self.connecting_peers)))
            Logger.write(3, "   CantConnect peers: " + str(len(self.cant_connect_peers)))
            Logger.write(3, "   Disconnected peers: " + str(len(self.disconnected_peers)))
            Logger.write(3, "   Complete list: " + str(len(self.complete_peer_list)))
            for peer in self.connected_peers:
                peer.log()

    def torrent_state_change(self, old_state, new_state):
        if new_state == TorrentState.Downloading:
            self.download_start = current_time()

    def add_potential_peers(self, uri, source):
        if len(self.potential_peers) > 1000:
            return

        if isinstance(uri, list):
            for u in uri:
                self.add_potential_peer_item(u, source)
        else:
            self.add_potential_peer_item(uri, source)

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

    def piece_done(self, piece_index):
        for peer in list(self.connected_peers):
            Logger.write(1, str(peer.id) + " Sending have message for piece " + str(piece_index))
            peer.connection_manager.send(HaveMessage(piece_index).to_bytes())

    def get_peer_by_id(self, peer_id):
        peers = [x for x in self.connected_peers if x.id == peer_id]
        if len(peers) != 0:
            return peers[0]
        return None

    def update_new_peers(self):
        if self.torrent.state != TorrentState.Downloading and self.torrent.state != TorrentState.DownloadingMetaData and self.torrent.state != TorrentState.WaitingUserFileSelection:
            return True

        if current_time() - self.last_peer_request > self.peer_request_interval or \
                                len(self.potential_peers) <= 10 and current_time() - self.last_peer_request > self.peer_request_interval_no_potential:
            Logger.write(2, "Requesting peers")
            EventManager.throw_event(EventType.RequestPeers, [self.torrent])
            self.last_peer_request = current_time()

        if current_time() - self.start_time > 45000 and not self.checked_no_peers:
            self.checked_no_peers = True

            if len(self.potential_peers) == 0 and \
                            len(self.connecting_peers) == 0 and \
                            len(self.connected_peers) == 0:
                Logger.write(2, "No peers found for torrent")
                EventManager.throw_event(EventType.NoPeers, [])
                return False

        peer_list = list(self.potential_peers)  # Try connecting to new peers from potential list
        if len(peer_list) == 0:
            peer_list = [x for x in self.disconnected_peers if current_time() - x[2] > 30000]  # If we dont have any new peers to try, try connecting to disconnected peers
            if len(peer_list) == 0:
                return True  # No peers available

        if len(self.connected_peers) >= self.max_peers_connected:
            # already have max connections
            return True

        if len(self.connecting_peers) >= self.max_peers_connecting:
            # already have max connecting
            return True

        connected_peers_under_max = self.max_peers_connected - len(self.connected_peers)
        connecting_peers_under_max = self.max_peers_connecting - len(self.connecting_peers)
        peers_to_connect = min(min(connecting_peers_under_max, connected_peers_under_max), len(peer_list))
        for index in range(peers_to_connect):
            if len(peer_list) == 0:
                # We probably stopped the torrent if this happens
                return True

            Logger.write(1, 'starting new peer')
            peer_to_connect = self.random.choice(peer_list)

            if peer_to_connect in self.potential_peers:
                self.potential_peers.remove(peer_to_connect)
            elif peer_to_connect in self.disconnected_peers:
                self.disconnected_peers.remove(peer_to_connect)

            peer_list.remove(peer_to_connect)
            self.__peer_id += 1
            new_peer = Peer(self.__peer_id, self.torrent, peer_to_connect[0], peer_to_connect[1])
            new_peer.start()
            self.connecting_peers.append(new_peer)

        return True

    def update_peer_status(self):
        peers_connected = [peer for peer in self.connecting_peers if peer.connection_state == ConnectionState.Connected]
        peers_failed_connect = [peer for peer in self.connecting_peers if peer.connection_state == ConnectionState.Disconnected and peer.connection_manager.connected_on == 0]
        peers_busy = [peer for peer in self.connecting_peers if peer.connection_state == ConnectionState.Disconnected and peer.connection_manager.connected_on != 0]
        peers_disconnected_connected = [peer for peer in self.connected_peers if peer.connection_state == ConnectionState.Disconnected]

        for peer in peers_connected:
            self.connecting_peers.remove(peer)
            self.connected_peers.append(peer)

        for peer in peers_busy:
            self.connecting_peers.remove(peer)
            self.disconnected_peers.append((peer.uri, peer.source, current_time(), 0))

        for peer in peers_failed_connect:
            self.connecting_peers.remove(peer)
            self.cant_connect_peers.append(peer.uri)

        for peer in peers_disconnected_connected:
            self.connected_peers.remove(peer)
            self.disconnected_peers.append((peer.uri, peer.source, current_time(), peer.counter.total))

        self.high_speed_peers = len([x for x in self.connected_peers if x.peer_speed == PeerSpeed.High])
        self.medium_speed_peers = len([x for x in self.connected_peers if x.peer_speed == PeerSpeed.Medium])
        self.connected_peers = sorted(self.connected_peers, key=lambda x: x.counter.value, reverse=True)
        self.disconnected_peers = sorted(self.disconnected_peers, key=lambda x: x[3], reverse=True)

        return True

    def update_bad_peers(self):
        if self.torrent.state != TorrentState.Downloading and self.torrent.state != TorrentState.DownloadingMetaData:
            return True

        if len(self.connected_peers) < self.max_peers_connected ** 0.66:
            return True  # Don't stop any peers if we have less than 66% of the max amount of peers

        if current_time() - self.download_start < 20000:
            return True  # Don't drop peers if we only recently started downloading again

        peers_to_check = [x for x in self.connected_peers if current_time() - x.connection_manager.connected_on > 30000]
        peers_to_check = sorted(peers_to_check, key=lambda x: x.counter.total)
        for peer in peers_to_check:
            if peer.counter.value > 5000:
                # If peer speed is more than 5kbps don't remove
                break

            Logger.write(2, "Stopping slowest peer to find a potential faster one. Peer speed last 5 seconds was " + str(write_size(peer.counter.value)) + ", total: " + str(write_size(peer.counter.total)))
            peer.stop()

        return True

    def get_peers_for_io(self):
        return list([x for x in self.connected_peers if x.connection_manager.connection_state == ConnectionState.Connected]), \
               list([x for x in self.connected_peers if len(x.connection_manager.to_send_bytes) > 0 and x.connection_manager.connection_state == ConnectionState.Connected])

    def are_fast_peers_available(self):
        return self.high_speed_peers > 0 or self.medium_speed_peers > 1

    def process_peer_messages(self):
        end_time = current_time() + 200
        index = 1

        for peer in [x for x in list(self.connected_peers) if x.connection_state == ConnectionState.Connected]:
            allowed_process_time = max(min(50, end_time - current_time()), 10)
            Logger.write(1, str(peer.id) + " peer with speed " + str(peer.counter.value) + " allowed " + str(allowed_process_time) + "ms at index " + str(index))
            if not peer.message_handler.update(allowed_process_time):
                Logger.write(1, str(peer.id) + " removing peer, update = false")
                self.connected_peers.remove(peer)
            index += 1
        Logger.write(1, "Total took " + str(current_time() - (end_time - 200)) + "ms")

        return True

    def stop(self):
        for peer in self.connecting_peers:
            peer.stop()
        for peer in self.connected_peers:
            peer.stop()

        self.complete_peer_list.clear()
        self.potential_peers.clear()
        self.cant_connect_peers.clear()
        self.update_peer_status()
        self.disconnected_peers.clear()
