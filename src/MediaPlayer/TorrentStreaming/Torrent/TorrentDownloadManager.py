from threading import Lock

import time
from pympler import asizeof

from MediaPlayer.TorrentStreaming.Torrent.Prioritizer import StreamPrioritizer
from MediaPlayer.Util.Enums import TorrentState, PeerSpeed, DownloadMode
from Shared.Events import EventManager, EventType
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Timing import Timing
from Shared.Util import current_time, write_size


class TorrentDownloadManager(LogObject):

    def __init__(self, torrent):
        super().__init__(torrent, "download")

        self.torrent = torrent
        self.prioritizer = StreamPrioritizer(self.torrent)

        self.init = False
        self.prio = False
        self.last_get_result = 0, 0
        self.last_get_time = 0
        self.upped_prios = []

        self.queue = []
        self.slow_peer_block_offset = 0
        self._ticks = 0

        self.download_mode = DownloadMode.Full
        self.peers_per_piece = [
            (100, 2, 5),
            (95, 1, 2),
            (0, 1, 1)
        ]

        self._event_id_log = EventManager.register_event(EventType.Log, self.log_queue)
        self._event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

        self.queue_log = ""

    def unregister(self):
        EventManager.deregister_event(self._event_id_stopped)
        EventManager.deregister_event(self._event_id_log)

    def check_size(self):
        for key, size in sorted([(key, asizeof.asizeof(value)) for key, value in self.__dict__.items()], key=lambda key_value: key_value[1], reverse=True):
            Logger().write(LogVerbosity.Important, "       Size of " + str(key) + ": " + write_size(size))

    def log_queue(self):
        Logger().write(LogVerbosity.Important, "-- TorrentDownloadManager state --")
        first = ""
        if self.queue:
            first = str(self.queue[0].index)
        Logger().write(LogVerbosity.Important, "     Queue status: length: " + str(len(self.queue)) + ", init: " + str(self.init) + ", prio: " + str(self.prio))
        Logger().write(LogVerbosity.Important, "     First in queue: " + first)
        Logger().write(LogVerbosity.Important, "     Last get_blocks: " + str(self.last_get_result[1]) + "/" + str(self.last_get_result[0]) + " " + str(current_time() - self.last_get_time) + "ms ago")
        if len(self.queue) > 0:
            blocks = [x for x in self.queue[0].blocks.values() if not x.done][0: 5]
            for block in blocks:
                Logger().write(LogVerbosity.Important, "     Block " + str(block.index) + " being downloaded by peers: " + ",".join([str(x.id) for x in block.peers_downloading]))

    def update(self):
        if self.torrent.state != TorrentState.Downloading:
            return True

        if not self.init:
            self.init = True
            self.requeue(0)

        return True

    def update_priority(self, full=False):
        if not self.init:
            return True

        if self.torrent.state == TorrentState.Done:
            if self.queue:
                self.queue = []
                self.queue_log = ""

            return True

        start_time = current_time()
        amount = 100
        if full:
            amount = len(self.torrent.data_manager._pieces)

        start = self.torrent.stream_position
        if full:
            start = self.torrent.media_file.start_piece(self.torrent.piece_length)

        pieces_to_look_at = self.torrent.data_manager.get_pieces_by_index_range(start, start + amount)

        for piece in pieces_to_look_at:
            piece.priority = self.prioritizer.prioritize_piece_index(piece.index)
        if full:
            self.queue = sorted(self.queue, key=lambda x: x.priority, reverse=True)
            first = "none"
            length = len(self.queue)
            if length > 0:
                first = str(self.queue[0].index)
            self.queue_log = "length: " + str(length) + ", first: " + first

        if self.queue:
            piece = self.queue[0]
            Logger().write(LogVerbosity.Debug, "Highest prio: " + str(piece.index) + ": "+str(piece.priority)+"% "
                            "("+str(piece.start_byte)+"-"+str(piece.end_byte)+"), took " + str(current_time()-start_time)+"ms, full: " + str(full))
        else:
            Logger().write(LogVerbosity.Debug, "No prio: queue empty")

        self.prio = True

        return True

    def requeue(self, start_position):
        Logger().write(LogVerbosity.All, "Starting download queue queuing")
        start_time = current_time()
        left = 0
        for piece in self.torrent.data_manager._pieces.values():
            if piece.start_byte > self.torrent.media_file.end_byte or piece.index < start_position or piece.end_byte < self.torrent.media_file.start_byte:
                continue

            if piece.persistent and piece.done:
                continue

            piece.reset()
            self.queue.append(piece)
            left += piece.length
            time.sleep(0)

        first = "none"
        length = len(self.queue)
        if length > 0:
            first = str(self.queue[0].index)
        self.queue_log = "length: " + str(length) + ", first: " + first

        self.slow_peer_block_offset = 15000000 // self.torrent.data_manager.piece_length # TODO Setting
        Logger().write(LogVerbosity.Debug, "Queueing took " + str(current_time() - start_time) + "ms for " + str(len(self.queue)) + " items")
        self.torrent.left = left

        self.update_priority(True)

    def get_allowed_fast_blocks_to_download(self, peer, amount):
        return []
        # can_download_pieces = []
        # result = []
        # piece_max_offset = 50000000 // self.torrent.data_manager.piece_length
        # if self.download_mode == DownloadMode.ImportantOnly:
        #     return result
        #
        # for piece_index in peer.allowed_fast_pieces:
        #     if piece_index > self.torrent.stream_position and piece_index - self.torrent.stream_position < piece_max_offset:
        #         if self.torrent.media_file is not None and piece_index > self.torrent.media_file.end_piece(self.torrent.data_manager.piece_length):
        #             continue
        #
        #         can_download_pieces.append(piece_index)
        #
        # if len(can_download_pieces) == 0:
        #     return result
        #
        # max_piece_index = max(can_download_pieces)
        # with self.queue_lock:
        #     for block_download in self.queue:
        #         if block_download.block.piece_index in can_download_pieces:
        #             if peer.bitfield.has_piece(block_download.block.piece_index) and peer not in block_download.peers:
        #                 result.append(block_download)
        #                 block_download.add_peer(peer)
        #
        #         if block_download.block.piece_index > max_piece_index and not block_download.block.persistent:
        #             break
        #
        #         if len(result) == amount:
        #             break
        #
        # return result

    def get_blocks_to_download(self, peer, amount):
        if self.torrent.state != TorrentState.Downloading:
            return []

        if not self.prio:
            return []

        Timing().start_timing("get_blocks")
        to_remove = []
        result = []
        piece_offset = 0

        if peer.peer_speed == PeerSpeed.Low:
            if self.torrent.peer_manager.are_fast_peers_available():
                # Slow peer; get block further down the queue
                piece_offset = self.slow_peer_block_offset
                if len(self.queue) < piece_offset:
                    piece_offset = max(len(self.queue) - 10, 0)

        skipped = 0
        removed = 0

        start = current_time()
        if self.torrent.end_game:
            queue_blocks = [x.blocks.values() for x in self.queue]
            total = []
            for block_list in queue_blocks:
                for block in block_list:
                    total.append(block)

            blocks = sorted([x for x in total if not x.done], key=lambda x: len(x.peers_downloading))
            for block in blocks:
                if peer in block.peers_downloading:
                    continue

                result.append(block)
                if len(result) == amount:
                    break
            return result

        queue = self.queue[piece_offset:]
        for piece in queue:
            if piece.done:
                to_remove.append(piece)
                removed += 1
            elif piece.priority == 0:
                to_remove.append(piece)
                removed += 1
            else:
                if not peer.bitfield.has_piece(piece.index):
                    skipped += 1
                    continue

                if self.download_mode == DownloadMode.ImportantOnly:
                    if piece.start_byte - self.torrent.stream_position * self.torrent.data_manager.piece_length > 100000000:
                        # The block is more than 100mb from our current position; don't download this
                        break

                for block in [x for x in piece.blocks.values() if not x.done]:
                    if len(block.peers_downloading) == 0:
                        result.append(block)

                    elif not self.torrent.starting:
                        if self.can_download_priority_pieces(block, peer, piece.priority):
                            result.append(block)
                    else:
                        skipped += 1

                    if len(result) == amount:
                        break
                if len(result) == amount:
                    break

        for piece in to_remove:
            self.queue.remove(piece)

        first = "none"
        length = len(self.queue)
        if length > 0:
            first = str(self.queue[0].index)
        self.queue_log = "length: " + str(length) + ", first: " + first

        Logger().write(LogVerbosity.All,
                       "Removed " + str(removed) + ", skipped " + str(skipped) + ", retrieved " + str(
                           len(result)) + ", queue length: " + str(len(self.queue)) + " took " + str(
                           current_time() - start) + "ms")

        if self._ticks == 100:
            self._ticks = 0
            Logger().write(LogVerbosity.Debug, "Removed " + str(removed) + ", skipped " + str(skipped) + ", retrieved " + str(len(result)) + ", queue length: " + str(len(self.queue)) + " took " + str(current_time() - start) + "ms")

        self._ticks += 1
        self.last_get_result = amount, len(result)
        self.last_get_time = current_time()
        Timing().stop_timing("get_blocks")
        return result

    def can_download_priority_pieces(self, block, peer, prio):
        if peer in block.peers_downloading:
            return False  # already downloading this

        if len([x for x in block.peers_downloading if x.peer_speed == PeerSpeed.High]) > 0:
            return False  # a high speed peer is already downloading this

        if peer.peer_speed != PeerSpeed.High and len([x for x in block.peers_downloading if x.peer_speed == PeerSpeed.Medium]) > 0:
            return False  # a medium speed peer is already downloading this and we're not fast ourselfs

        if self.torrent.end_game:
            return True

        currently_downloading = len(block.peers_downloading)

        if self.download_mode == DownloadMode.ImportantOnly:
            if prio == 100:
                return True
            return currently_downloading < 5

        return self.allowed_download(prio, currently_downloading, peer.peer_speed)

    def allowed_download(self, priority, current, speed):
        for prio, slow, fast in self.peers_per_piece:
            if priority < prio:
                continue
            if speed == PeerSpeed.Low:
                return current < slow
            else:
                return current < fast

    def seek(self, old_index, new_piece_index):
        start_time = current_time()
        Logger().write(LogVerbosity.Info, "Seeking " + str(old_index) + " to " + str(new_piece_index) + ", pre-seek queue has " + str(len(self.queue)) + " items")

        self.queue = []
        first = "none"
        length = len(self.queue)
        if length > 0:
            first = str(self.queue[0].index)
        self.queue_log = "length: " + str(length) + ", first: " + first

        if self.torrent.state == TorrentState.Done:
            self.torrent.restart_downloading()

        self.requeue(new_piece_index)

        Logger().write(LogVerbosity.Debug, "Seeking done in " + str(current_time() - start_time) + "ms, post-seek queue has " + str(len(self.queue)) + " items")

    def redownload_piece(self, piece):
        self.torrent.left += piece.length
        self.queue.insert(0, piece)
        length = len(self.queue)
        first = str(self.queue[0].index)
        self.queue_log = "length: " + str(length) + ", first: " + first

    def stop(self):
        self.prioritizer.stop()
        self.torrent = None
