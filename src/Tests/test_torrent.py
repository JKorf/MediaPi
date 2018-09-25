from MediaPlayer.Torrent.Torrent import Torrent


def test_magnet_uri():
    magnet_uri = "magnet:?xt=urn:btih:e2e457b2e77128cd20fafd0837bbdb9a4d543578&dn=Solo.A.Star.Wars.Story.2018.1080p.BRRip.x264-MP4&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969&tr=udp%3A%2F%2Fzer0day.ch%3A1337&tr=udp%3A%2F%2Fopen.demonii.com%3A1337&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Fexodus.desync.com%3A6969"
    success, torrent = Torrent.from_magnet(1, magnet_uri)

    assert success
    assert torrent.name == "Solo.A.Star.Wars.Story.2018.1080p.BRRip.x264-MP4"
