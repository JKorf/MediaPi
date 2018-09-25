import json

import time

from MediaPlayer.Torrent.Torrent import Torrent
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time
from WebServer.Controllers.TorrentController import TorrentController
from WebServer.Providers import TorrentProvider


def test_downloading_start():
    Logger.set_log_level(Settings.get_int("log_level"))
    top_torrents = json.loads(TorrentController.top())
    torrent = Torrent.from_magnet(1, TorrentProvider.Torrent.get_magnet_uri(top_torrents[0]['url']))[1]
    torrent.start()
    start_time = current_time()
    while current_time() - start_time < 30000:
        if torrent.download_counter.total > 0:
            break
        time.sleep(1)
    assert torrent.download_counter.total > 0

