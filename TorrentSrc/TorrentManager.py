from Shared.Events import EventManager, EventType
from TorrentSrc.Torrent.Torrent import Torrent
from TorrentSrc.Util.Enums import OutputMode
from TorrentSrc.Util.Threading import CustomThread


class TorrentManager:

    __torrent_id = 0

    @property
    def total_speed(self):
        total = 0
        for torrent in list(self.torrents):
            total += torrent.download_counter.value
        return total

    @property
    def stream_buffer_ready(self):
        for torrent in list(self.torrents):
            if torrent.output_mode == OutputMode.Stream:
                return torrent.bytes_ready_in_buffer
        return -1

    def __init__(self):
        self.torrents = []

        EventManager.register_event(EventType.StartTorrent, self.start_torrent)
        EventManager.register_event(EventType.StopTorrent, self.remove_torrent)
        EventManager.register_event(EventType.StopStreamTorrent, self.remove_stream_torrent)

    def get_by_id(self, id):
        for torrent in list(self.torrents):
            if torrent.id == id:
                return torrent

    def add_torrent(self, torrent):
        self.torrents.append(torrent)

    def remove_stream_torrent(self):
        for torrent in self.torrents:
            if torrent.output_mode == OutputMode.Stream:
                self.remove_torrent(torrent.id)

    def remove_torrent(self, id):
        torrent = [x for x in self.torrents if x.id == id]
        if len(torrent) == 0:
            return

        torrent[0].stop()
        self.torrents.remove(torrent[0])

        if torrent[0].output_mode == OutputMode.Stream:
            EventManager.throw_event(EventType.StreamTorrentStopped, [torrent[0]])

    def start_torrent(self, url, output_mode):
        TorrentManager.__torrent_id += 1

        success, torrent = Torrent.create_torrent(TorrentManager.__torrent_id, url, output_mode)
        if success:
            self.add_torrent(torrent)
            torrent.start()
            if torrent.output_mode == OutputMode.Stream:
                EventManager.throw_event(EventType.StreamTorrentStarted, [torrent])
        else:
            EventManager.throw_event(EventType.InvalidTorrent, ["Invalid uri"])
        return torrent


