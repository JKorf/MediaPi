from threading import Lock

from MediaPlayer.TorrentStreaming.Torrent.Prioritizer import StreamPrioritizer
from MediaPlayer.Util.Enums import TorrentState, PeerSpeed, DownloadMode
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Util import current_time


class TorrentDownloadManager:

    def __init__(self, torrent):
        self.torrent = torrent
        self.prioritizer = StreamPrioritizer(self.torrent)

        self.init = False
        self.prio = False
        self.last_get_result = 0, 0
        self.last_get_time = 0
        self.upped_prios = []

        self.queue = []
        self.queue_lock = Lock()
        self.slow_peer_block_offset = 0
        self.ticks = 0

        self.download_mode = DownloadMode.Full
        self.peers_per_piece = [
            (100, 2, 5),
            (95, 1, 2),
            (0, 1, 1)
        ]

        self.event_id_log = EventManager.register_event(EventType.Log, self.log_queue)
        self.event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

    def unregister(self):
        EventManager.deregister_event(self.event_id_stopped)
        EventManager.deregister_event(self.event_id_log)

    def log_queue(self):
        with Logger.lock:
            Logger.write(3, "-- TorrentDownloadManager state --")
            first = ""
            if self.queue:
                first = str(self.queue[0].block.piece_index) + "-" + str(self.queue[0].block.block_index_in_piece)
            Logger.write(3, "     Queue status: length: " + str(len(self.queue)) + ", init: " + str(self.init) + ", prio: " + str(self.prio))
            Logger.write(3, "     First in queue: " + first)
            Logger.write(3, "     Last get_blocks: " + str(self.last_get_result[1]) + "/" + str(self.last_get_result[0]) + " " + str(current_time() - self.last_get_time) + "ms ago")

    def up_priority(self, piece_index):
        self.upped_prios.append(piece_index)
        self.update_priority(True)

    def update(self):
        if self.torrent.state != TorrentState.Downloading:
            return True

        if not self.init:
            self.init = True
            self.requeue(0)

        return True

    def update_priority(self, full=False, lock=True):
        if not self.init:
            return True
        if lock:
            self.queue_lock.acquire()

        if self.torrent.state == TorrentState.Done:
            if self.queue:
                self.queue = []

            if lock:
                self.queue_lock.release()
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
            self.queue = sorted(self.queue, key=lambda x: x.piece.priority, reverse=True)

        if self.queue:
            block_download = self.queue[0]
            Logger.write(2, "Highest prio: " + str(block_download.block.piece_index) + ": "+str(block_download.piece.priority)+"% "
                            "("+str(block_download.piece.start_byte)+"-"+str(block_download.piece.end_byte)+"), took " + str(current_time()-start_time)+"ms, full: " + str(full))
        else:
            Logger.write(2, "No prio: queue empty")

        if lock:
            self.queue_lock.release()
        self.prio = True

        return True

    def requeue(self, start_position):
        Logger.write(2, "Starting download queue queuing")
        start_time = current_time()
        left = 0
        for piece in self.torrent.data_manager._pieces.values():
            if piece.start_byte > self.torrent.media_file.end_byte or piece.index < start_position or piece.end_byte < self.torrent.media_file.start_byte:
                continue

            if piece.persistent and piece.done:
                continue

            piece.reset()
            for block in piece.blocks.values():
                self.queue.append(BlockDownload(block, piece))
                left += block.length

        self.slow_peer_block_offset = 15000000 // self.torrent.data_manager.block_size # TODO Setting
        Logger.write(2, "Queueing took " + str(current_time() - start_time) + "ms for " + str(len(self.queue)) + " items")
        self.torrent.left = left

        self.update_priority(True, False)

    def get_allowed_fast_blocks_to_download(self, peer, amount):
        can_download_pieces = []
        result = []
        piece_max_offset = 50000000 // self.torrent.data_manager.piece_length
        if self.download_mode == DownloadMode.ImportantOnly:
            return result

        for piece_index in peer.allowed_fast_pieces:
            if piece_index > self.torrent.stream_position and piece_index - self.torrent.stream_position < piece_max_offset:
                if self.torrent.media_file is not None and piece_index > self.torrent.media_file.end_piece(self.torrent.data_manager.piece_length):
                    continue

                can_download_pieces.append(piece_index)

        if len(can_download_pieces) == 0:
            return result

        max_piece_index = max(can_download_pieces)
        with self.queue_lock:
            for block_download in self.queue:
                if block_download.block.piece_index in can_download_pieces:
                    if peer.bitfield.has_piece(block_download.block.piece_index) and peer not in block_download.peers:
                        result.append(block_download)
                        block_download.add_peer(peer)

                if block_download.block.piece_index > max_piece_index and not block_download.block.persistent:
                    break

                if len(result) == amount:
                    break

        return result

    def get_blocks_to_download(self, peer, amount):
        if self.torrent.state != TorrentState.Downloading:
            return []

        if not self.prio:
            return []

        to_remove = []
        result = []
        block_offset = 0

        if peer.peer_speed == PeerSpeed.Low:
            if self.torrent.peer_manager.are_fast_peers_available():
                # Slow peer; get block further down the queue
                block_offset = self.slow_peer_block_offset
                if len(self.queue) < block_offset:
                    block_offset = max(len(self.queue) - 10, 0)

        skipped = 0
        removed = 0

        with self.queue_lock:
            start = current_time()

            queue = self.queue[block_offset:]
            if self.torrent.end_game:
                queue.sort(key=lambda x: len(x.peers))

            for block_download in queue:
                if block_download.block.done:
                    to_remove.append(block_download)
                    removed += 1
                elif block_download.piece.priority == 0:
                    to_remove.append(block_download)
                    removed += 1
                else:
                    if not peer.bitfield.has_piece(block_download.block.piece_index):
                        skipped += 1
                        continue

                    if len(block_download.peers) == 0:
                        result.append(block_download)
                        block_download.add_peer(peer)

                    elif not self.torrent.starting:
                        if self.can_download_priority_pieces(block_download, peer):
                            result.append(block_download)
                            block_download.add_peer(peer)

                    elif self.download_mode == DownloadMode.ImportantOnly:
                        if block_download.block.start_byte_total - self.torrent.stream_position * self.torrent.data_manager.piece_length > 100000000:
                            # The block is more than 100mb from our current position; don't download this
                            break
                    else:
                        skipped += 1

                    if len(result) == amount:
                        break

            for block_download in to_remove:
                self.queue.remove(block_download)

            if self.ticks == 100:
                self.ticks = 0
                Logger.write(2, "Removed " + str(removed) + ", skipped " + str(skipped) + ", retrieved " + str(len(result)) + ", queue length: " + str(len(self.queue)) + " took " + str(current_time() - start) + "ms")

            self.ticks += 1
            self.last_get_result = amount, len(result)
            self.last_get_time = current_time()
        return result

    def can_download_priority_pieces(self, block_download, peer):
        if peer in block_download.peers:
            return False  # already downloading this

        if len([x for x in block_download.peers if x.peer_speed == PeerSpeed.High]) > 0:
            return False  # a high speed peer is already downloading this

        if peer.peer_speed != PeerSpeed.High and len([x for x in block_download.peers if x.peer_speed == PeerSpeed.Medium]) > 0:
            return False  # a medium speed peer is already downloading this and we're not fast ourselfs

        if self.torrent.end_game:
            return True

        currently_downloading = len(block_download.peers)
        prio = block_download.piece.priority

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
        Logger.write(2, "Seeking " + str(old_index) + " to " + str(new_piece_index) + ", now " + str(len(self.queue)) + " items")
        with self.queue_lock:
            self.queue = []

            if self.torrent.state == TorrentState.Done:
                self.torrent.restart_downloading()

            self.requeue(new_piece_index)

        Logger.write(2, "Seeking done in " + str(current_time() - start_time) + "ms for " + str(len(self.queue)) + " items")

    def redownload_piece(self, piece):
        with self.queue_lock:
            for block in piece.blocks.values():
                self.torrent.left += block.length
                block_download = BlockDownload(block, piece)
                self.queue.insert(0, block_download)

    def stop(self):
        self.prioritizer.stop()
        self.torrent = None

class BlockDownload:

    def __init__(self, block, piece):
        self.block = block
        self.piece = piece
        self.peers = []
        self.lock = Lock()

    def add_peer(self, peer):
        self.lock.acquire()
        self.peers.append(peer)
        self.lock.release()

    def remove_peer(self, peer):
        self.lock.acquire()
        self.peers.remove(peer)
        self.lock.release()
