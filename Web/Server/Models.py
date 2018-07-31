import os

from os.path import isfile, join

from TorrentSrc.Util.Util import write_size


class current_media:

    def __init__(self, state, type, title, path, img, playing_for, play_time, volume, length, selected_sub, subtitles, sub_delay, subs_done, audio_tracks, current_audio_track, buffered_percentage):
        self.state = state
        self.type = type
        self.title = title
        self.path = path
        self.img = img
        self.playing_for = playing_for
        self.play_time = play_time
        self.volume = volume
        self.length = length
        self.subs_done = subs_done
        self.selected_sub = selected_sub
        self.subtitles = subtitles
        self.subtitle_delay = sub_delay
        self.audio_tracks = audio_tracks
        self.current_audio_track = current_audio_track
        self.buffered = buffered_percentage


class FileStructure:

    def __init__(self, path, just_files=False):
        self.dirs = []
        self.files = []
        self.path = path

        if just_files:
            self.files = [f for f in os.listdir(path) if isfile(join(path, f)) and f.endswith(('.jpg', '.gif', 'png', 'mp4', 'avi'))]
        else:
            for(dirpath, dirnames, filenames) in os.walk(path):
                self.dirs.extend(dirnames)
                self.files.extend(filenames)
                break


class DebugInfo:

    def __init__(self, potential, connected, size, downloaded, speed, buffer_ready, buffer_total, bytes_streamed,
                 torrent_state, stream_position, stream_buffer_position, threads, cpu, memory, left_to_download, overhead):
        self.potential = potential
        self.connected = connected
        self.size = write_size(size)
        self.downloaded = write_size(downloaded)
        self.speed = write_size(speed)
        self.stream_buffer_ready = write_size(buffer_ready)
        self.stream_buffer_total = write_size(buffer_total)
        self.torrent_state = torrent_state
        self.stream_position = stream_position
        self.stream_buffer_position = stream_buffer_position
        self.bytes_streamed = write_size(bytes_streamed)
        self.threads = threads
        self.cpu = cpu
        self.memory = memory
        self.dht_nodes = 0
        self.left_to_download = write_size(left_to_download)
        self.overhead = write_size(overhead)

    def add_dht(self, nodes):
        self.dht_nodes = nodes


class Info:

    def __init__(self, running_for, peers_attempted, peers_failed, peers_succeeded, peers_from_dht, peers_from_udp_tracker, peers_from_http_tracker, peers_from_pex,
                 total_downloaded, threads_started, subs_downloaded, play_time, max_download):
        self.running_for = running_for
        self.peers_attempted = peers_attempted
        self.peers_failed = peers_failed
        self.peers_succeeded = peers_succeeded
        self.peers_from_dht = peers_from_dht
        self.peers_from_udp_tracker = peers_from_udp_tracker
        self.peers_from_http_tracker = peers_from_http_tracker
        self.peers_from_pex = peers_from_pex
        self.total_downloaded = total_downloaded
        self.threads_started = threads_started
        self.subs_downloaded = subs_downloaded
        self.play_time = play_time
        self.max_download = max_download


class Status:

    def __init__(self, total_speed, buffer_ready, cpu, memory):
        self.speed = total_speed
        self.buffer_ready = buffer_ready
        self.cpu = cpu
        self.memory = memory


class Settings:

    def __init__(self, raspberry, gui, external_trackers, max_sub_files):
        self.raspberry = raspberry
        self.gui = gui
        self.external_trackers = external_trackers
        self.max_sub_files = max_sub_files


class WebSocketMessage:

    def __init__(self, type, evnt, data):
        self.type = type
        self.event = evnt
        self.data = data


class Version:

    def __init__(self, build_date, version_number):
        self.build_date = build_date
        self.version_number = version_number


class StartUp:

    def __init__(self, instance_name):
        self.instance_name = instance_name


class TorrentModel:

    def __init__(self, title, seeders, leechers, size, url, category):
        self.title = title
        self.seeders = seeders
        self.leechers = leechers
        self.size = size
        self.url = url
        if "movie" in category.lower():
            self.category = "movie"
        elif "show" in category.lower():
            self.category = "show"
        else:
            self.category = "other"


class TorrentDetailModel:

    def __init__(self):
        self.id = 0
        self.name = None
        self.state = 0
        self.potential_peers = 0
        self.connected_peers = 0
        self.connecting_peers = 0

        self.size = 0
        self.percentage_done = 0
        self.downloaded = 0
        self.left = 0
        self.speed = 0

        self.stream_buffer_ready = 0
        self.stream_buffer_total = 0
        self.streamed = 0

    @classmethod
    def from_torrent(cls, torrent):
        model = TorrentDetailModel()
        model.id = torrent.id
        model.name = torrent.name
        model.state = torrent.state

        model.potential_peers = len(torrent.peer_manager.potential_peers)
        model.connected_peers = len(torrent.peer_manager.connected_peers)
        model.connecting_peers = len(torrent.peer_manager.connecting_peers)

        model.size = write_size(torrent.total_size)
        model.percentage_done = torrent.percentage_done
        model.downloaded = write_size(torrent.download_counter.total)
        model.left = write_size(torrent.left)
        model.speed = write_size(torrent.download_counter.value)

        model.streaming = True
        model.stream_buffer_ready = write_size(torrent.bytes_ready_in_buffer)
        model.stream_buffer_total = write_size(torrent.bytes_total_in_buffer)
        model.streamed = write_size(torrent.bytes_streamed)
        return model


class MediaFile:

    def __init__(self, path, size, season, episode):
        self.path = path
        self.size = write_size(size)
        self.season = season
        self.episode = episode
