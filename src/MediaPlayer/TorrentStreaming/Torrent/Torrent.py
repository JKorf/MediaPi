import base64
import hashlib
import math
import urllib.parse
import urllib.request
from threading import Lock
from pympler import asizeof

from MediaPlayer.TorrentStreaming.Torrent.TorrentDataManager import TorrentDataManager
from MediaPlayer.TorrentStreaming.Torrent.TorrentDownloadManager import TorrentDownloadManager
from MediaPlayer.TorrentStreaming.Torrent.TorrentMetadataManager import TorrentMetadataManager
from MediaPlayer.TorrentStreaming.Torrent.TorrentNetworkManager import TorrentNetworkManager
from MediaPlayer.TorrentStreaming.Torrent.TorrentOutputManager import TorrentOutputManager
from MediaPlayer.TorrentStreaming.Tracker.Tracker import TrackerManager

from MediaPlayer.TorrentStreaming.Torrent.TorrentPeerManager import TorrentPeerManager
from MediaPlayer.Util import Bencode
from MediaPlayer.Util.Bencode import BTFailure
from MediaPlayer.Util.Enums import TorrentState
from MediaPlayer.Util.Util import try_parse_season_episode, is_media_file
from Shared import Engine
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Util import headers, write_size, current_time


class Torrent:

    @property
    def stream_speed(self):
        return self.output_manager.stream_manager.stream_speed

    @property
    def left(self):
        return self.to_download_bytes

    @left.setter
    def left(self, value):
        self.to_download_bytes = value

    @property
    def bytes_ready_in_buffer(self):
        return self.output_manager.stream_manager.consecutive_pieces_total_length

    @property
    def bytes_total_in_buffer(self):
        return self.output_manager.stream_manager.bytes_in_buffer

    @property
    def stream_position(self):
        return self.output_manager.stream_manager.stream_position_piece_index

    @property
    def stream_buffer_position(self):
        return self.output_manager.stream_manager.consecutive_pieces_last_index

    @property
    def bytes_streamed(self):
        return self.output_manager.stream_manager.listener.bytes_send

    @property
    def end_game(self):
        # TODO setting
        if self.left < 2000000:
            return True
        return False

    @property
    def starting(self):
        # TODO setting
        if self.network_manager.average_download_counter.total < 4000000:
            return True
        return False

    @property
    def state(self):
        return self.__state

    @property
    def is_executing(self):
        return self.__state == TorrentState.Downloading \
               or self.__state == TorrentState.Paused

    @property
    def is_preparing(self):
        return self.__state == TorrentState.Initial \
               or self.__state == TorrentState.DownloadingMetaData \
               or self.__state == TorrentState.WaitingUserFileSelection

    def __init__(self, id, uri):
        self.name = None
        self.id = id
        self.uri = uri
        self.total_size = 0
        self.uploaded = 0
        self.piece_length = 0
        self.piece_hashes = None
        self.announce_uris = []
        self.info_hash = None
        self.files = []
        self.__state = TorrentState.Initial
        self.__lock = Lock()

        self.media_file = None
        self.selected_media_file = None

        self.stream_file_hash = None
        self.to_download_bytes = 0
        self.overhead = 0

        self.user_file_selected_id = EventManager.register_event(EventType.TorrentMediaFileSelection, self.user_file_selected)
        self.log_id = EventManager.register_event(EventType.Log, self.log)

        self.engine = Engine.Engine('Main Engine', 500)
        self.message_engine = Engine.Engine('Peer Message Engine', 200)

        self.tracker_manager = TrackerManager()
        self.peer_manager = TorrentPeerManager(self)
        self.data_manager = TorrentDataManager(self)
        self.download_manager = TorrentDownloadManager(self)
        self.output_manager = TorrentOutputManager(self)
        self.metadata_manager = TorrentMetadataManager(self)
        self.network_manager = TorrentNetworkManager(self)

    def check_size(self):
        for key, value, size in sorted([(key, value, asizeof.asizeof(value)) for key, value in self.__dict__.items()], key=lambda key_value: key_value[2], reverse=True):
            Logger().write(LogVerbosity.Important, "   Size of " + str(key) + ": " + write_size(size))
            if getattr(value, "check_size", None) is not None:
                value.check_size()

    @classmethod
    def create_torrent(cls, id, url):
        if url.startswith("magnet:"):
            return Torrent.from_magnet(id, url)
        elif url.startswith("http://"):
            return Torrent.from_torrent_url(id, url)
        else:
            return Torrent.from_file(id, url)

    @classmethod
    def from_torrent_url(cls, id, uri):
        torrent = Torrent(id, uri)
        torrent.from_magnet = False
        try:
            request = urllib.request.Request(urllib.parse.unquote_plus(uri), None, headers)
            file = urllib.request.urlopen(request).read()
        except:
            Logger().write(LogVerbosity.Important, "Error downloading torrent file: " + urllib.parse.unquote_plus(uri))
            return False, torrent

        try:
            meta_info = Bencode.bdecode(file)
        except BTFailure:
            Logger().write(LogVerbosity.Important, "Invalid torrent file")
            return False, torrent

        if b'info' not in meta_info:
            Logger().write(LogVerbosity.Important, "Invalid bencoded torrent dictionary")
            return False, torrent

        info = meta_info[b'info']
        torrent.parse_torrent_file(meta_info)
        torrent.info_hash = InfoHash.from_info_dict(info)

        return True, torrent

    @classmethod
    def from_file(cls, id, file_path):
        torrent = Torrent(id, file_path)
        torrent.from_magnet = False
        try:
            file = open(file_path, 'rb')
        except IOError:
            Logger().write(LogVerbosity.Important, "Torrent file could not be opened: " + file_path)
            return False, torrent

        try:
            meta_info = Bencode.bdecode(file.read())
        except BTFailure:
            Logger().write(LogVerbosity.Important, "Invalid torrent file")
            return False, torrent

        if b'info' not in meta_info:
            Logger().write(LogVerbosity.Important, "Invalid bencoded torrent dictionary")
            return False, torrent

        info = meta_info[b'info']
        torrent.parse_torrent_file(meta_info)
        torrent.info_hash = InfoHash.from_info_dict(info)

        return True, torrent

    @classmethod
    def from_magnet(cls, id, uri):
        torrent = Torrent(id, uri)
        torrent.from_magnet = True
        if not torrent.parse_magnet_uri(uri):
            return False, torrent

        return True, torrent

    def start(self):
        Logger().write(LogVerbosity.Info, 'Starting torrent')
        if self.from_magnet:
            self.__set_state(TorrentState.DownloadingMetaData)
        else:
            self.__set_state(TorrentState.Downloading)

        self.engine.add_work_item("peer_manager_new", 1000, self.peer_manager.update_new_peers)
        self.engine.add_work_item("peer_manager_status", 500, self.peer_manager.update_peer_status)
        self.engine.add_work_item("peer_manager_bad_peers", 30000, self.peer_manager.update_bad_peers)
        self.engine.add_work_item("torrent_download_manager", 5000, self.download_manager.update)
        self.engine.add_work_item("torrent_download_manager_prio", 5000, self.download_manager.update_priority)
        self.engine.add_work_item("output_manager", 1000, self.output_manager.update)
        self.engine.add_work_item("piece_validator", 500, self.data_manager.piece_hash_validator.update)
        self.engine.add_work_item("stream_manager", 3000, self.output_manager.stream_manager.update)
        self.engine.add_work_item("check_download_speed", 1000, self.check_download_speed)
        self.engine.add_work_item("cleanup_used_pieces", 5000, self.data_manager.cleanup_used_pieces)

        self.message_engine.add_work_item("data_manager", 200, self.data_manager.update_write_blocks)
        self.message_engine.add_work_item("peer_messages", 200, self.peer_manager.process_peer_messages)

        self.engine.start()
        self.message_engine.start()
        self.network_manager.start()
        Logger().write(LogVerbosity.Important, "Torrent started")

    def parse_info_dictionary(self, info_dict):
        self.name = info_dict[b'name'].decode('utf8')

        if b'files' in info_dict:
            # Multifile
            files = info_dict[b'files']
            total_length = 0
            for file in files:
                file_length = file[b'length']
                path = self.name
                path_list = file[b'path']
                last_path = ""
                for path_part in path_list:
                    path += "/" + path_part.decode('utf8')
                    last_path = path_part.decode('utf8')

                fi = TorrentDownloadFile(file_length, total_length, last_path, path, is_media_file(path))
                self.files.append(fi)

                total_length += file_length
                Logger().write(LogVerbosity.Info, "File: " + fi.path)
        else:
            # Singlefile
            total_length = info_dict[b'length']
            file = TorrentDownloadFile(total_length, 0, self.name, self.name, is_media_file(self.name))
            self.files.append(file)
            Logger().write(LogVerbosity.Info, "File: " + file.path)

        self.piece_length = info_dict[b'piece length']
        self.piece_hashes = info_dict[b'pieces']
        self.total_size = total_length
        media_files = [x for x in self.files if x.is_media]
        if len(media_files) == 0:
            # No media file, can't play so just stop
            Logger().write(LogVerbosity.Important, "No media file found in torrent, stopping")
            EventManager.throw_event(EventType.StopPlayer, [])
        elif len(media_files) == 1:
            # Single media file, just play that
            self.set_media_file(media_files[0].path)
        elif self.selected_media_file is not None:
            self.set_media_file([x for x in media_files if x.name == self.selected_media_file][0].path)
        else:
            ordered = sorted(media_files, key=lambda x: x.length, reverse=True)
            biggest = ordered[0]
            second = ordered[1]
            if biggest.length > second.length * 8:
                # One file is significantly bigger than the others, play that
                self.set_media_file(biggest.path)
            else:
                # Multiple files, let user decide
                self.__set_state(TorrentState.WaitingUserFileSelection)
                for file in media_files:
                    season, epi = try_parse_season_episode(file.path)
                    if season:
                        file.season = season
                    if epi:
                        file.episode = epi
                EventManager.throw_event(EventType.TorrentMediaSelectionRequired, [media_files])

        Logger().write(LogVerbosity.Info, "Torrent metadata read")

    def set_selected_media_file(self, file):
        self.selected_media_file = file

    def set_media_file(self, path):
        self.media_file = [x for x in self.files if x.path == path][0]
        Logger().write(LogVerbosity.Info, "Media file: " + str(self.media_file.name) + ", " + str(self.media_file.start_byte) + " - " + str(self.media_file.end_byte) + "/" + str(self.total_size))

        self.data_manager.set_piece_info(self.piece_length, self.piece_hashes)
        self.__set_state(TorrentState.Downloading)
        self.to_download_bytes = self.data_manager.get_piece_by_offset(self.media_file.end_byte).end_byte - self.data_manager.get_piece_by_offset(self.media_file.start_byte).start_byte
        Logger().write(LogVerbosity.Info, "To download: " + str(self.to_download_bytes) + " (" + str(self.to_download_bytes - self.media_file.length) + " overhead), piece length: " + str(self.piece_length))
        EventManager.throw_event(EventType.TorrentMediaFileSet, [self.media_file.name])

    def user_file_selected(self, file_path):
        Logger().write(LogVerbosity.Info, "User selected media file: " + file_path)
        file = [x for x in self.files if x.path == file_path][0]
        self.set_media_file(file)

    def parse_torrent_file(self, decoded_dict):
        for uri_list in decoded_dict[b'announce-list']:
            self.announce_uris.append(uri_list[0].decode('utf8'))

        self.parse_info_dictionary(decoded_dict[b'info'])

    def parse_magnet_uri(self, uri):
        uri = urllib.parse.unquote_plus(uri)

        if not uri.startswith('magnet:?xt=urn:btih:'):
            Logger().write(LogVerbosity.Important, 'Invalid magnet uri ' + uri)
            return False

        protocol_stripped = uri[8:]
        param_split = protocol_stripped.split("&")
        infohash_prot = param_split[0]
        self.info_hash = InfoHash.from_url_encoded(infohash_prot[12:])

        for parm in param_split:
            key_value = parm.split("=")
            if key_value[0] == 'dn':
                self.name = key_value[1]
            if key_value[0] == 'tr':
                self.announce_uris.append(urllib.parse.unquote_plus(key_value[1]))

        return True

    def restart_downloading(self):
        self.__set_state(TorrentState.Downloading)

    def pause(self):
        self.__set_state(TorrentState.Paused)

    def unpause(self):
        self.__set_state(TorrentState.Downloading)

    def torrent_done(self):
        Logger().write(LogVerbosity.Important, 'Torrent is done')
        self.output_manager.flush()
        self.to_download_bytes = 0
        self.__set_state(TorrentState.Done)

    def __set_state(self, value):
        Logger().write(LogVerbosity.Info, "Setting torrent state from " + TorrentState.get_str(self.__state) + " to " + TorrentState.get_str(value))
        old = self.__state
        self.__state = value
        EventManager.throw_event(EventType.TorrentStateChange, [old, value])

    def get_data_bytes_for_stream(self, start_byte, length):
        return self.output_manager.stream_manager.get_data_for_stream(start_byte + self.media_file.start_byte, length)

    def get_data_bytes_for_hash(self, start_byte, length):
        return self.data_manager.get_data_bytes_for_hash(start_byte + self.media_file.start_byte, length)

    def check_download_speed(self):
        current_max = Stats.total('max_download_speed')
        current_speed = self.network_manager.live_download_counter.value
        if current_speed > current_max:
            Stats.set('max_download_speed', current_speed)
        return True

    def log(self):
        pass

    def stop(self):
        if self.__state == TorrentState.Stopping:
            return

        Logger().write(LogVerbosity.Info, 'Torrent stopping')
        self.__set_state(TorrentState.Stopping)
        EventManager.deregister_event(self.user_file_selected_id)
        EventManager.deregister_event(self.log_id)

        self.engine.stop()
        self.message_engine.stop()
        Logger().write(LogVerbosity.Debug, 'Torrent engines stopped')

        self.output_manager.stop()
        self.peer_manager.stop()
        self.tracker_manager.stop()
        self.download_manager.stop()
        self.data_manager.stop()
        self.network_manager.stop()
        self.metadata_manager.stop()
        Logger().write(LogVerbosity.Debug, 'Torrent managers stopped')

        for file in self.files:
            file.close()

        self.engine = None
        self.message_engine = None
        self.tracker_manager = None
        self.peer_manager = None
        self.data_manager = None
        self.download_manager = None
        self.output_manager = None
        self.metadata_manager = None
        self.network_manager = None

        EventManager.throw_event(EventType.TorrentStopped, [])
        Logger().write(LogVerbosity.Important, 'Torrent stopped')


class InfoHash:

    def __init__(self):
        self.sha1_hashed_bytes = None
        self.url_encoded = None

    @classmethod
    def from_info_dict(cls, info_dict):
        infohash = InfoHash()
        infohash.sha1_hashed_bytes = hashlib.sha1(Bencode.bencode(info_dict)).digest()
        infohash.url_encoded = urllib.parse.quote_plus(infohash.sha1_hashed_bytes)
        return infohash

    @classmethod
    def from_url_encoded(cls, url):
        unquoted = urllib.parse.unquote_plus(url)
        infohash = InfoHash()
        infohash.url_encoded = url
        if len(url) == 32:
            infohash.sha1_hashed_bytes = base64.b32decode(unquoted)
        else:
            infohash.sha1_hashed_bytes = bytes(bytearray.fromhex(unquoted))
        return infohash


class TorrentDownloadFile:

    def __init__(self, length, start_byte, name, path, is_media):
        self.length = length
        self.start_byte = start_byte
        self.end_byte = start_byte + length
        self.path = path
        self.name = name
        self.stream = None
        self.done = False
        self.is_media = is_media
        self.first_64k = None
        self.last_64k = None
        self.played_for = 0
        self.play_length = 0

        self.season = 0
        self.episode = 0

        self.__lock = Lock()

    def open(self):
        if self.stream is None:
            self.stream = open(self.path, 'wb')

    def close(self):
        if self.stream is not None:
            self.stream.close()

    def start_piece(self, piece_length):
        return math.floor(self.start_byte / piece_length)

    def end_piece(self, piece_length):
        return math.floor(self.end_byte / piece_length)

    def write_file(self, data):
        offset = 0
        for piece in data:
            self.write(offset, piece.get_data())
            offset += piece.length
        self.stream.close()
        self.done = True
        Logger().write(LogVerbosity.Important, "File " + self.name + " done")

    def write(self, offset_in_file, data):
        with self.__lock:
            self.open()

            self.stream.seek(offset_in_file)
            can_write = len(data)
            if self.length - offset_in_file < can_write:
                can_write = self.length - offset_in_file

            self.stream.write(data[0:can_write])
            self.stream.flush()

        return can_write
