import time

from Interface.TV.VLCPlayer import PlayerState
from MediaPlayer.DHT.DHTEngine import DHTEngine
from MediaPlayer.Subtitles.SubtitleProvider import SubtitleProvider
from MediaPlayer.Torrent.Torrent import Torrent
from Shared.Events import EventType, EventManager
from Shared.Logger import Logger
from Shared.Settings import Settings


class TorrentManager:

    def __init__(self, start):
        self.start = start
        self.torrent = None
        self.subtitle_provider = SubtitleProvider(self.start)

        self.dht_enabled = Settings.get_bool("dht")
        if self.dht_enabled:
            self.dht = DHTEngine()
            self.dht.start()
            EventManager.register_event(EventType.RequestDHTPeers, self.request_dht_peers)

        EventManager.register_event(EventType.StartTorrent, self.start_torrent)
        EventManager.register_event(EventType.StopTorrent, self.stop_torrent)
        EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)
        EventManager.register_event(EventType.NewDHTNode, self.new_dht_node)

    def start_torrent(self, url, media_file):
        if self.torrent is not None:
            Logger.write(2, "Can't start new torrent, still torrent active")
            return

        success, torrent = Torrent.create_torrent(1, url)
        if success:
            self.torrent = torrent
            if media_file is not None:
                self.torrent.set_selected_media_file(media_file)
            torrent.start()
        else:
            Logger.write(2, "Invalid torrent")
            EventManager.throw_event(EventType.Error, ["torrent_error", "Invalid torrent"])
            if self.torrent is not None:
                self.torrent.stop()
                self.torrent = None

            time.sleep(1)

    def player_state_change(self, old_state, new_state):
        if new_state == PlayerState.Ended:
            if self.torrent is not None:
                self.torrent.stop()
                Logger.write(2, "Ended " + self.torrent.media_file.name)
                self.torrent = None

    def stop_torrent(self):
        if self.torrent:
            self.torrent.stop()
            self.torrent = None

    def new_dht_node(self, ip, port):
        if self.dht_enabled:
            self.dht.add_node_by_ip_port(ip, port)

    def request_dht_peers(self, torrent):
        if self.dht_enabled:
            self.dht.get_peers(torrent, self.add_peers_from_dht)

    def add_peers_from_dht(self, torrent, peers):
        torrent.peer_manager.add_potential_peers_from_ip_port(peers)