import os

from os.path import isfile, join

from Shared.Util import write_size


class CurrentMedia:

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


class MediaInfo:

    def __init__(self, potential, connected, size, downloaded, speed, buffer_ready, buffer_total, bytes_streamed,
                 torrent_state, stream_position, stream_buffer_position, threads, left_to_download, overhead):
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
        self.dht_nodes = 0
        self.left_to_download = write_size(left_to_download)
        self.overhead = write_size(overhead)

    def add_dht(self, nodes):
        self.dht_nodes = nodes


class Info:

    def __init__(self, running_for, peers_attempted, peers_failed, peers_succeeded, peers_from_dht, peers_from_udp_tracker, peers_from_http_tracker, peers_from_pex,
                 total_downloaded, subs_downloaded, play_time, max_download, connected_dht, connected_udp, connected_http, connected_pex):
        self.running_for = running_for
        self.peers_attempted = peers_attempted
        self.peers_failed = peers_failed
        self.peers_succeeded = peers_succeeded

        self.peers_from_dht = peers_from_dht
        self.peers_from_udp_tracker = peers_from_udp_tracker
        self.peers_from_http_tracker = peers_from_http_tracker
        self.peers_from_pex = peers_from_pex
        self.peers_from_dht_connected = connected_dht
        self.peers_from_udp_tracker_connected = connected_udp
        self.peers_from_http_tracker_connected = connected_http
        self.peers_from_pex_connected = connected_pex

        self.total_downloaded = total_downloaded
        self.subs_downloaded = subs_downloaded
        self.play_time = play_time
        self.max_download = max_download


class Status:

    def __init__(self, total_speed, buffer_ready, cpu, memory, torrent_state, peers_connected, potential_peers):
        self.speed = total_speed
        self.buffer_ready = buffer_ready
        self.cpu = cpu
        self.memory = memory
        self.torrent_state = torrent_state
        self.peers_connected = peers_connected
        self.potential_peers = potential_peers


class Settings:

    def __init__(self, raspberry, gui, external_trackers, max_sub_files):
        self.raspberry = raspberry
        self.gui = gui
        self.external_trackers = external_trackers
        self.max_sub_files = max_sub_files


# class WebSocketMessage:
#
#     def __init__(self, evnt, topic, data):
#         self.event = evnt
#         self.topic = topic
#         self.data = data

class WebSocketRequestMessage:

    def __init__(self, id, instance_id, info_type, data):
        self.id = id
        self.instance_id = instance_id
        self.type = "request"
        self.info_type = info_type
        self.data = data

class WebSocketInvalidMessage:

    def __init__(self, id, info_type):
        self.id = id
        self.type = "invalid"
        self.info_type = info_type

class WebSocketUpdateMessage:

    def __init__(self, sub_id, data):
        self.type = "update"
        self.subscription_id = sub_id
        self.data = data

class WebSocketResponseMessage:
    def __init__(self, request_id, data):
        self.type = "response"
        self.request_id = request_id
        self.data = data

class WebSocketInitMessage:
    def __init__(self, name):
        self.type = "Slave"
        self.event = "init"
        self.data = name

class WebSocketSlaveRequest:
    def __init__(self, valid_for, type, data):
        self.event = "slave_request"
        self.type = type
        self.valid_for = valid_for
        self.data = data

class WebSocketSlaveMessage:
    def __init__(self, topic, data):
        self.event = "update"
        self.topic = topic
        self.data = data

class WebSocketSlaveCommand:
    def __init__(self, topic, parameters):
        self.event = "command"
        self.topic = topic
        self.parameters = parameters

class Version:

    def __init__(self, build_date):
        self.build_date = build_date


class StartUp:

    def __init__(self, instance_name, lighting_enabled):
        self.instance_name = instance_name
        self.lighting_enabled = lighting_enabled


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

    def __init__(self, path, title, size, season, episode, type, media_file, img, seen):
        self.path = path
        self.title = title
        self.size = write_size(size)
        self.season = season
        self.episode = episode
        self.type = type
        self.media_file = media_file
        self.img = img
        self.seen = seen


class LightControl:

    def __init__(self, index, application_type, last_seen, reachable, lights):
        self.application_type = application_type
        self.last_seen = last_seen
        self.reachable = reachable
        self.lights = lights
        self.index = index


class LightDevice:

    def __init__(self, supports_dimmer, supports_temp, supports_color, state, dimmer, color_temp, hex_color):
        self.supports_dimmer = supports_dimmer
        self.supports_temp = supports_temp
        self.supports_color = supports_color
        self.state = state
        self.dimmer = dimmer
        self.color_temp = color_temp
        self.hex_color = hex_color


class CecDevice:

    def __init__(self):
        self.address = None
        self.active = False
        self.vendor = None
        self.osd = None


class Media:

    def __init__(self, type, id, title, path, file, image, start_time, season=0, episode=0):
        self.image = image
        self.id = id
        self.title = title
        self.path = path
        self.file = file
        self.type = type
        self.start_time = start_time
        self.season = season
        self.episode = episode

class BaseMedia:

    def __init__(self, id, poster, title):
        self.id = id
        self.poster = poster
        self.title = title