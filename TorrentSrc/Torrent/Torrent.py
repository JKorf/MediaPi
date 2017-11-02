import base64
import hashlib
import os
import urllib.parse
import urllib.request
from threading import Lock

import math

from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Engine import Engine
from TorrentSrc.Torrent.TorrentPeerManager import TorrentPeerManager
from TorrentSrc.Torrent.TorrentDataManager import TorrentDataManager
from TorrentSrc.Torrent.TorrentDownloadManager import TorrentDownloadManager
from TorrentSrc.Torrent.TorrentMetadataManager import TorrentMetadataManager
from TorrentSrc.Torrent.TorrentNetworkManager import TorrentNetworkManager
from TorrentSrc.Torrent.TorrentOutputManager import TorrentOutputManager
from TorrentSrc.Tracker.Tracker import TrackerManager
from TorrentSrc.Util import Bencode
from TorrentSrc.Util.Bencode import BTFailure
from TorrentSrc.Util.Counter import Counter
from TorrentSrc.Util.Enums import TorrentState, OutputMode
from TorrentSrc.Util.Util import headers


class Torrent:

    @property
    def left(self):
        return self.to_download_bytes

    @left.setter
    def left(self, value):
        self.to_download_bytes = value

    @property
    def percentage_done(self):
        if self.total_size == 0:
            return 0
        return round((self.download_counter.total / self.total_size) * 100, 2)

    @property
    def bytes_ready_in_buffer(self):
        if self.output_mode == OutputMode.File:
            return 0
        return self.output_manager.output_writer.consecutive_pieces_total_length

    @property
    def bytes_total_in_buffer(self):
        if self.output_mode == OutputMode.File:
            return 0
        return self.output_manager.output_writer.bytes_in_buffer

    @property
    def stream_position(self):
        if self.output_mode == OutputMode.File:
            return 0
        return self.output_manager.output_writer.stream_position_piece_index

    @property
    def stream_buffer_position(self):
        if self.output_mode == OutputMode.File:
            return 0
        return self.output_manager.output_writer.consecutive_pieces_last_index

    @property
    def last_byte_requested(self):
        if self.output_mode == OutputMode.File:
            return 0
        return self.output_manager.output_writer.last_request

    @property
    def streamserver_running(self):
        return self.output_manager.output_writer.listener.running

    @property
    def bytes_streamed(self):
        if self.output_mode == OutputMode.File:
            return 0
        return self.output_manager.output_writer.listener.bytes_send

    @property
    def bytes_missing_for_buffering(self):
        missing = 5000000
        for piece in self.data_manager.pieces:
            if piece.start_byte > 5000000:
                return missing
            for block in piece.blocks:
                if block.start_byte_total > 5000000:
                    return missing
                if block.done:
                    missing -= block.length

        return 0

    @property
    def end_game(self):
        # TODO setting
        if self.left < 2000000:
            return True
        return False

    def __init__(self, id, output_mode):
        self.name = None
        self.id = id
        self.total_size = 0
        self.uploaded = 0
        self.piece_length = 0
        self.piece_hashes = None
        self.available_leechers = 0
        self.available_seeders = 0
        self.announce_uris = []
        self.info_hash = None
        self.files = []
        self.state = TorrentState.Initial
        self.output_mode = output_mode
        self.__lock = Lock()
        self.media_file = None
        self.stream_file_hash = None
        self.to_download_bytes = 0
        self.outstanding_requests = 0

        self.engine = Engine.Engine('Main Engine', Settings.get_int("main_engine_tick_rate"))
        self.download_counter = Counter()

        self.tracker_manager = TrackerManager(self)
        self.peer_manager = TorrentPeerManager(self)
        self.data_manager = TorrentDataManager(self)
        self.download_manager = TorrentDownloadManager(self)
        self.output_manager = TorrentOutputManager(self)
        self.metadata_manager = TorrentMetadataManager(self)
        self.network_manager = TorrentNetworkManager(self)

    @classmethod
    def create_torrent(cls, id, url, output_mode):
        if url.startswith("magnet:"):
            return Torrent.from_magnet(id, url, output_mode)
        elif url.startswith("http://"):
            return Torrent.from_torrent_url(id, url, output_mode)
        else:
            return Torrent.from_file(id, url, output_mode)

    @classmethod
    def from_torrent_url(cls, id, url, output_mode):
        torrent = Torrent(id, output_mode)
        torrent.from_magnet = False
        try:
            request = urllib.request.Request(urllib.parse.unquote_plus(url), None, headers)
            file = urllib.request.urlopen(request).read()
        except:
            Logger.write(3, "Error downloading torrent file: " + urllib.parse.unquote_plus(url), 'error')
            return False, torrent

        try:
            meta_info = Bencode.bdecode(file)
        except BTFailure:
            Logger.write(3, "Invalid torrent file", 'error')
            return False, torrent

        if b'info' not in meta_info:
            Logger.write(3, "Invalid bencoded torrent dictionary", 'error')
            return False, torrent

        info = meta_info[b'info']
        torrent.parse_torrent_file(meta_info)
        torrent.info_hash = InfoHash.from_info_dict(info)

        return True, torrent

    @classmethod
    def from_file(cls, id, file_path, output_mode):
        torrent = Torrent(id, output_mode)
        torrent.from_magnet = False
        try:
            file = open(file_path, 'rb')
        except IOError:
            Logger.write(3, "Torrent file could not be opened: " + file_path)
            return False, torrent

        try:
            meta_info = Bencode.bdecode(file.read())
        except BTFailure:
            Logger.write(3, "Invalid torrent file", 'error')
            return False, torrent

        if b'info' not in meta_info:
            Logger.write(3, "Invalid bencoded torrent dictionary", 'error')
            return False, torrent

        info = meta_info[b'info']
        torrent.parse_torrent_file(meta_info)
        torrent.info_hash = InfoHash.from_info_dict(info)

        return True, torrent

    @classmethod
    def from_magnet(cls, id, uri, output_mode):
        torrent = Torrent(id, output_mode)
        torrent.from_magnet = True
        if not torrent.parse_magnet_uri(uri):
            return False, torrent

        Logger.write(3, "Torrent created: " + uri)
        return True, torrent

    def start(self):
        Logger.write(2, 'Starting engine')
        if self.from_magnet:
            self.state = TorrentState.DownloadingMetaData
        else:
            self.state = TorrentState.Downloading

        self.engine.queue_repeating_work_item("tracker_manager", 10000, self.tracker_manager.update)
        self.engine.queue_repeating_work_item("peer_manager_new", 1000, self.peer_manager.update_new_peers)
        self.engine.queue_repeating_work_item("peer_manager_status", 1000, self.peer_manager.update_peer_status)
        self.engine.queue_repeating_work_item("peer_manager_bad_peers", 30000, self.peer_manager.update_bad_peers)
        self.engine.queue_repeating_work_item("torrent_download_manager", 5000, self.download_manager.update)
        self.engine.queue_repeating_work_item("torrent_download_manager_prio", 5000, self.download_manager.update_priority)
        self.engine.queue_repeating_work_item("output_manager", 1000, self.output_manager.update)
        self.engine.queue_repeating_work_item("counter", 1000, self.download_counter.update)
        self.engine.queue_repeating_work_item("data_manager", 200, self.data_manager.update_write_blocks)
        self.engine.queue_repeating_work_item("piece_validator", 500, self.data_manager.piece_hash_validator.update)
        if self.output_mode == OutputMode.Stream:
            self.engine.queue_repeating_work_item("output_writer", 1000, self.output_manager.output_writer.update)

        self.engine.start()
        self.network_manager.start()
        Logger.write(3, "Torrent started")

    def parse_info_dictionary(self, info_dict):
        self.name = info_dict[b'name'].decode('ascii')
        to_disk = self.output_mode == OutputMode.File
        download_folder = Settings.get_string("download_folder")

        if b'files' in info_dict:
            # Multifile
            files = info_dict[b'files']
            total_length = 0
            for file in files:
                file_length = file[b'length']
                path = download_folder + self.name
                path_list = file[b'path']
                last_path = ""
                for path_part in path_list:
                    path += "\\" + path_part.decode('ascii')
                    last_path = path_part.decode('ascii')

                fi = TorrentDownloadFile(file_length, total_length, last_path, path, to_disk)
                self.files.append(fi)
                ext = os.path.splitext(path)[1]
                if (ext == ".mp4" or ext == ".mkv" or ext == ".avi") and (self.media_file is None or self.media_file.length < file_length):
                    self.media_file = fi
                total_length += file_length
        else:
            # Singlefile
            total_length = info_dict[b'length']
            file = TorrentDownloadFile(total_length, 0, self.name, download_folder + self.name, to_disk)
            self.media_file = file
            self.files.append(file)

        Logger.write(2, "Stream file " + str(self.media_file.start_byte) + " - " + str(self.media_file.end_byte) + "/" + str(total_length))
        self.piece_length = info_dict[b'piece length']
        self.piece_hashes = info_dict[b'pieces']
        self.total_size = total_length
        self.data_manager.set_piece_info(self.piece_length, self.piece_hashes)
        self.state = TorrentState.Downloading
        self.to_download_bytes = self.data_manager.get_piece_by_offset(self.media_file.end_byte).end_byte - self.data_manager.get_piece_by_offset(self.media_file.start_byte).start_byte
        Logger.write(2, "To download: " + str(self.to_download_bytes))
        Logger.write(3, "Torrent metadata read")

    def parse_torrent_file(self, decoded_dict):
        for uri_list in decoded_dict[b'announce-list']:
            self.announce_uris.append(uri_list[0].decode('ascii'))

        self.parse_info_dictionary(decoded_dict[b'info'])

    def parse_magnet_uri(self, uri):
        uri = urllib.parse.unquote_plus(uri)

        if not uri.startswith('magnet:?xt=urn:btih:'):
            Logger.write(3, 'Invalid magnet uri ' + uri, 'error')
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

    def pause(self):
        Logger.write(3, 'Torrent paused')
        self.state = TorrentState.Paused

    def unpause(self):
        Logger.write(3, 'Torrent unpaused')
        self.state = TorrentState.Downloading

    def get_data_bytes_for_stream(self, start_byte, length):
        return self.output_manager.output_writer.get_data_for_stream(start_byte + self.media_file.start_byte, length)

    def get_data_bytes_for_hash(self, start_byte, length):
        return self.data_manager.get_data_bytes_for_hash(start_byte + self.media_file.start_byte, length)

    def torrent_done(self):
        Logger.write(3, 'Torrent is done')
        self.output_manager.flush()
        self.to_download_bytes = 0
        self.state = TorrentState.Done

    def stop(self):
        Logger.write(2, 'Torrent stopping')
        self.engine.stop()
        self.output_manager.stop()
        self.peer_manager.stop()
        self.tracker_manager.stop()
        self.network_manager.stop()
        Logger.write(3, 'Torrent stopped')


class InfoHash:

    def __init__(self):
        self.sha1_hashed_bytes = None
        self.url_encoded = None

    @classmethod
    def from_info_dict(cls, dict):
        infohash = InfoHash()
        infohash.sha1_hashed_bytes = hashlib.sha1(Bencode.bencode(dict)).digest()
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

    def __init__(self, length, start_byte, name, path, output_to_disk):
        self.length = length
        self.start_byte = start_byte
        self.end_byte = start_byte + length
        self.path = path
        self.name = name
        self.stream = None
        self.__lock = Lock()

        if output_to_disk:
            directory = os.path.dirname(self.path)
            if not os.path.exists(directory):
                os.makedirs(directory)

    def open(self):
        if self.stream is None:
            self.stream = open(self.path, 'wb')

    def start_piece(self, piece_length):
        return math.floor(self.start_byte / piece_length)

    def end_piece(self, piece_length):
        return math.floor(self.end_byte / piece_length)

    def write(self, offset_in_file, data):
        self.open()

        self.__lock.acquire()

        self.stream.seek(offset_in_file)
        can_write = len(data)
        if self.length - offset_in_file < can_write:
            can_write = self.length - offset_in_file

        self.stream.write(data[0:can_write])
        self.stream.flush()

        self.__lock.release()
        return can_write

