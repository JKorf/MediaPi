from Shared.LogObject import LogObject


class TorrentManager(LogObject):

    def __init__(self, torrent, name):
        super().__init__(torrent, name)
        self.torrent = torrent

    def stop(self):
        self.torrent = None
