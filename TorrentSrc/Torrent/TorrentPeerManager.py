from random import Random
from urllib.parse import urlparse

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Util import current_time
from TorrentSrc.Peer.Peer import Peer
from TorrentSrc.Peer.PeerMessages import HaveMessage
from TorrentSrc.Util.Enums import ConnectionState, PeerSpeed, TorrentState, PeerSource
from TorrentSrc.Util.Util import write_size


class TorrentPeerManager:

    __peer_id = 0

    @property
    def connected_peer_list(self):
        return list(self.connected_peers)

    def __init__(self, torrent):
        self.torrent = torrent
        self.potential_peers = []
        self.connecting_peers = []
        self.connected_peers = []
        self.disconnected_peers = []
        self.max_peers_connected = Settings.get_int("max_peers_connected")
        self.max_peers_connecting = Settings.get_int("max_peers_connecting")
        self.random = Random()
        self.fast_peers = 0
        self.disconnect_peer_timeout = 0

        self.event_id_log = EventManager.register_event(EventType.Log, self.log_peers)
        self.event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

        self.high_speed_peers = 0
        self.medium_speed_peers = 0

    def unregister(self):
        EventManager.deregister_event(self.event_id_log)
        EventManager.deregister_event(self.event_id_stopped)

    def log_peers(self):
        Logger.lock.acquire()
        Logger.write(3, "-- TorrentPeerManager state --")
        for peer in self.connected_peers:
            Logger.write(3, "     " + str(peer.id) + " | " + peer.communication_state.print() + " | " + str(peer.peer_speed) + "("+ write_size(peer.counter.value) + ")" + " | Outstanding: " + str(len(peer.download_manager.downloading)))
            peer.log()
        Logger.lock.release()

    def add_potential_peers_from_ip_port(self, data):
        for ip, port in data:
            self.add_potential_peers("tcp://" + ip + ":" + str(port), PeerSource.DHT)

    def add_potential_peers(self, uri, source):
        if len(self.potential_peers) > 1000:
            return

        if isinstance(uri, list):
            for u in uri:
                if uri not in [x[0] for x in self.potential_peers]:
                    self.potential_peers.append((u, source))
                    self.add_potential_peer_stat(source)
        else:
            if uri not in [x[0] for x in self.potential_peers]:
                self.potential_peers.append((uri, source))
                self.add_potential_peer_stat(source)

    def add_potential_peer_stat(self, source):
        if source == PeerSource.DHT:
            Stats['peers_source_dht'].add(1)
        elif source == PeerSource.HttpTracker:
            Stats['peers_source_http_tracker'].add(1)
        elif source == PeerSource.UdpTracker:
            Stats['peers_source_udp_tracker'].add(1)
        elif source == PeerSource.PeerExchange:
            Stats['peers_source_exchange'].add(1)

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
        if self.torrent.state != TorrentState.Downloading and self.torrent.state != TorrentState.DownloadingMetaData:
            return True

        if len(self.potential_peers) == 0:
            # no new peers
            return True

        if len(self.connected_peers) >= self.max_peers_connected:
            # already have max connections
            return True

        if len(self.connecting_peers) >= self.max_peers_connecting:
            # already have max connecting
            return True

        connected_peers_under_max = self.max_peers_connected - len(self.connected_peers)
        connecting_peers_under_max = self.max_peers_connecting - len(self.connecting_peers)
        peers_to_connect = min(min(connecting_peers_under_max, connected_peers_under_max), len(self.potential_peers))
        for index in range(peers_to_connect):
            if len(self.potential_peers) == 0:
                # We probably stopped the torrent if this happens
                return True

            Logger.write(1, 'starting new peer')
            peer_to_connect = self.random.choice(self.potential_peers)
            self.potential_peers.remove(peer_to_connect)
            self.__peer_id += 1
            new_peer = Peer(self.__peer_id, self.torrent, urlparse(peer_to_connect[0]), peer_to_connect[1])
            new_peer.start()
            self.connecting_peers.append(new_peer)

        return True

    def update_peer_status(self):
        peers_connected = [peer for peer in self.connecting_peers if peer.connection_manager.connection_state == ConnectionState.Connected]
        peers_disconnected = [peer for peer in self.connecting_peers if peer.connection_manager.connection_state == ConnectionState.Disconnected]
        peers_disconnected_connected = [peer for peer in self.connected_peers if peer.connection_manager.connection_state == ConnectionState.Disconnected]

        for peer in peers_connected:
            self.connecting_peers.remove(peer)
            self.connected_peers.append(peer)

        for peer in peers_disconnected:
            self.connecting_peers.remove(peer)
            self.disconnected_peers.append(peer.uri)

        for peer in peers_disconnected_connected:
            self.connected_peers.remove(peer)
            self.disconnected_peers.append(peer.uri)

        self.high_speed_peers = len([x for x in self.connected_peers if x.peer_speed == PeerSpeed.High])
        self.medium_speed_peers = len([x for x in self.connected_peers if x.peer_speed == PeerSpeed.Medium])

        return True

    def update_bad_peers(self):
        if self.torrent.state != TorrentState.Downloading and self.torrent.state != TorrentState.DownloadingMetaData:
            return True

        if self.disconnect_peer_timeout > current_time():
            return True

        to_stop = len(self.connected_peers) - 25
        if to_stop > 0:
            peers_to_check = [x for x in self.connected_peers if current_time() - x.connection_manager.connected_on > 30000]
            peers_to_check = sorted(peers_to_check, key=lambda x: x.counter.total)
            for peer in peers_to_check:
                if peer.counter.value > 5000:
                    # If peer speed is more than 5kbps don't remove
                    continue

                Logger.write(2, "Stopping slowest peer to find a potential faster one. Peer speed last 5 seconds was " + str(write_size(peer.counter.value)) + ", total: " + str(write_size(peer.counter.total)))
                peer.stop()
                to_stop -= 1

                if to_stop == 0:
                    break

        return True

    def get_peers_for_io(self):
        return list([x for x in self.connected_peers if x.connection_manager.connection_state == ConnectionState.Connected]), \
               list([x for x in self.connected_peers if len(x.connection_manager.to_send_bytes) > 0 and x.connection_manager.connection_state == ConnectionState.Connected])

    def are_fast_peers_available(self):
        return self.high_speed_peers > 0 or self.medium_speed_peers > 1

    def stop(self):
        for peer in self.connecting_peers:
            peer.stop()
        for peer in self.connected_peers:
            peer.stop()

        self.potential_peers.clear()
        self.update_peer_status()
        self.disconnected_peers.clear()
