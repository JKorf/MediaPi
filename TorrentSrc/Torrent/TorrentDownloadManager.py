from threading import Lock

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time
from TorrentSrc.Torrent.Prioritizer import StreamPrioritizer, FilePrioritizer
from TorrentSrc.Util.Enums import OutputMode, TorrentState, PeerSpeed, DownloadMode


class TorrentDownloadManager:

    def __init__(self, torrent):
        self.torrent = torrent
        if self.torrent.output_mode == OutputMode.File:
            self.prioritizer = FilePrioritizer(self.torrent)
        else:
            self.prioritizer = StreamPrioritizer(self.torrent)

        self.init = False
        self.prio = False
        self.queue = []
        self.queue_lock = Lock()
        self.slow_peer_block_offset = 0
        self.ticks = 0

        self.download_mode = DownloadMode.Full

    def update(self):
        if self.torrent.state != TorrentState.Downloading:
            return True

        if not self.init:
            self.init = True
            self.initialize()

        return True

    def update_priority(self, full=False, lock=True):
        if not self.init:
            return True

        if self.torrent.state == TorrentState.Done:
            return True

        if lock:
            self.queue_lock.acquire()

        amount = 100
        if full:
            amount = len(self.torrent.data_manager.pieces)

        pieces_to_look_at = self.torrent.data_manager.pieces[self.torrent.stream_position: self.torrent.stream_position + amount]
        for piece in pieces_to_look_at:
            piece.priority = self.prioritizer.prioritize_piece_index(piece.index)
        if full:
            self.queue = sorted(self.queue, key=lambda x: self.torrent.data_manager.pieces[x.block.piece_index].priority, reverse=True)

        if self.queue:
            block_download = self.queue[0]
            Logger.write(1, "Highest prio: " + str(block_download.block.piece_index) + "("+str(self.torrent.data_manager.pieces[block_download.block.piece_index].priority)+"%)")

        if lock:
            self.queue_lock.release()
        self.prio = True

        return True

    def initialize(self):
        Logger.write(2, "Starting init")
        start_time = current_time()
        for piece in self.torrent.data_manager.pieces:
            if piece.start_byte > self.torrent.media_file.end_byte or piece.end_byte < self.torrent.media_file.start_byte:
                continue
            for block in piece.blocks:
                self.queue.append(BlockDownload(block))

        self.slow_peer_block_offset = 15000000 // self.torrent.data_manager.block_size # TODO Setting
        Logger.write(2, "Initial queueing took " + str(current_time() - start_time) + "ms for " + str(len(self.queue)) + " items")

        self.update_priority(True)

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

        self.queue_lock.acquire()
        start = current_time()

        queue = self.queue[block_offset:]
        if self.torrent.end_game:
            queue.sort(key=lambda x: len(x.peers))

        for block_download in queue:
            if block_download.block.done:
                to_remove.append(block_download)
                removed += 1
            elif self.torrent.data_manager.pieces[block_download.block.piece_index].priority == 0:
                to_remove.append(block_download)
                removed += 1
            else:
                if not peer.bitfield.has_piece(block_download.block.piece_index):
                    skipped += 1
                    continue

                if len(block_download.peers) == 0:
                    result.append(block_download)
                    block_download.add_peer(peer)

                elif self.can_download_priority_pieces(block_download, peer):
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
            Logger.write(2, "Removed " + str(removed) + ", skipped " + str(skipped) + ", took " + str(current_time() - start) + "ms")

        self.ticks += 1
        self.queue_lock.release()
        return result

    def can_download_priority_pieces(self, block_download, peer):
        if peer in block_download.peers:
            return False
        currently_downloading = len(block_download.peers)
        if self.torrent.end_game:
            if currently_downloading > 5:
                return False
        else:
            if self.torrent.data_manager.pieces[block_download.block.piece_index].priority < 100:
                if self.download_mode != DownloadMode.ImportantOnly:
                    return False

            if currently_downloading > 3:
                if peer.peer_speed == PeerSpeed.Low:
                    return False
            else:
                if currently_downloading > 1:
                    if peer.peer_speed == PeerSpeed.Low and self.torrent.peer_manager.are_fast_peers_available():
                        return False

        return True

    def seek(self, old_index, new_piece_index):
        start_time = current_time()
        Logger.write(2, "Seeking " + str(old_index) + " to " + str(new_piece_index))
        self.queue_lock.acquire()

        if new_piece_index > old_index:
            # Seeking forwards
            Logger.write(2, "Seeking forwards")
            to_remove = []
            for block_download in self.queue:
                if block_download.block.piece_index < new_piece_index:
                    to_remove.append(block_download)
                else:
                    break

            for block_download in to_remove:
                self.queue.remove(block_download)
                if not block_download.block.done:
                    self.torrent.left -= block_download.block.length

        else:
            # Seeking back
            Logger.write(2, "Seeking backwards")
            blocks_to_redo = []
            for piece in self.torrent.data_manager.pieces[new_piece_index: old_index + 1]:
                if not piece.persistent:
                    piece.done = False
                    for block in piece.blocks:
                        self.torrent.left += block.length
                        block.done = False
                        blocks_to_redo.append(block)

            Logger.write(2, "Need to redo " + str(len(blocks_to_redo)))
            Logger.write(2, "Queue before: " + str(len(self.queue)))
            self.queue = [x for x in self.queue if x.block not in blocks_to_redo]
            Logger.write(2, "Queue after1: " + str(len(self.queue)))

            for block in blocks_to_redo:
                self.queue.append(BlockDownload(block))
            Logger.write(2, "Queue after2: " + str(len(self.queue)))

        self.prio = False

        self.update_priority(True, False)

        self.queue_lock.release()
        Logger.write(2, "Seeking done in " + str(current_time() - start_time) + "ms for " + str(len(self.queue)) + " items")

    def redownload_piece(self, piece):
        self.queue_lock.acquire()
        for block in piece.blocks:
            self.torrent.left += block.length
            block_download = BlockDownload(block)
            self.queue.insert(0, block_download)

        self.queue_lock.release()


class BlockDownload:

    def __init__(self, block):
        self.block = block
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
