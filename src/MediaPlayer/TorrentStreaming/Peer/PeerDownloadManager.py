from threading import Lock

from MediaPlayer.TorrentStreaming.Peer.PeerMessages import RequestMessage
from MediaPlayer.Util.Enums import ConnectionState, PeerSpeed, PeerInterestedState, PeerChokeState
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Util import current_time, write_size


class PeerDownloadManager:

    @property
    def max_blocks(self):
        if self.peer.peer_speed == PeerSpeed.Low:
            return self.low_peer_max_blocks
        elif self.peer.peer_speed == PeerSpeed.Medium:
            return self.medium_peer_max_blocks
        return self.fast_peer_max_blocks

    def __init__(self, peer):
        self.peer = peer
        self.stopped = False
        self.downloading = []
        self.lock = Lock()
        self.blocks_done_lock = Lock()
        self.blocks_done = []

        block_size = Settings.get_int("block_size")
        self.low_peer_max_blocks = Settings.get_int("low_peer_max_download_buffer") // block_size
        self.medium_peer_max_blocks = Settings.get_int("medium_peer_max_download_buffer") // block_size
        self.fast_peer_max_blocks = Settings.get_int("fast_peer_max_download_buffer") // block_size

    def update(self):
        if self.peer.connection_state != ConnectionState.Connected:
            return True

        self.check_current_downloading()

        if not self.has_interesting_pieces():
            return True

        if self.peer.communication_state.out_interest == PeerInterestedState.Uninterested:
            return True

        if len(self.downloading) >= self.max_blocks:
            return True

        if self.peer.communication_state.in_choke == PeerChokeState.Choked:
            if len(self.peer.allowed_fast_pieces) == 0:
                return True

            with self.lock:
                new_blocks = self.max_blocks - len(self.downloading)
                to_download = self.peer.torrent.download_manager.get_allowed_fast_blocks_to_download(self.peer, new_blocks)
                for block in to_download:
                    self.downloading.append((block, current_time()))

                if len(to_download) == 0:
                    return True

                Logger().write(LogVerbosity.Debug, str(self.peer.id) + " requesting " + str(len(to_download)) + " allowed fast blocks")
                self.request(to_download)
                return True

        with self.lock:
            if self.stopped:
                return False

            new_blocks = self.max_blocks - len(self.downloading)
            to_download = self.peer.torrent.download_manager.get_blocks_to_download(self.peer, new_blocks)
            for block in to_download:
                self.downloading.append((block, current_time()))

            self.request(to_download)

        return True

    def request(self, to_download):
        Logger().write(LogVerbosity.Debug, str(self.peer.id) + " going to request " + str(len(to_download)) + " blocks")
        for block in to_download:
            block.add_downloader(self.peer)
            request = RequestMessage(block.piece_index, block.start_byte_in_piece, block.length)
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Sending request for piece ' + str(request.index) + ", block " + str(
                request.offset // 16384))
            self.peer.connection_manager.send(request.to_bytes())

    def block_done(self, block_offset):
        with self.blocks_done_lock:
            self.blocks_done.append(block_offset)

    def check_current_downloading(self):
        canceled = 0

        done_copy = list(self.blocks_done)
        with self.lock:
            if self.stopped:
                return False

            for block, request_time in list(self.downloading):
                if block.start_byte_total in done_copy:  # Peer downloaded this block; it's done
                    self.downloading = [x for x in self.downloading if not x[0].index == block.index]
                    block.remove_downloader(self.peer)
                    done_copy.remove(block.start_byte_total)
                    continue

                block_prio = self.peer.torrent.data_manager._pieces[block.piece_index].priority
                prio_timeout = self.get_priority_timeout(block_prio)
                passed_time = current_time() - request_time
                if passed_time > prio_timeout:
                    self.downloading = [x for x in self.downloading if not x[0].index == block.index]
                    block.remove_downloader(self.peer)
                    canceled += 1

                with self.blocks_done_lock:
                    self.blocks_done = [x for x in self.blocks_done if x not in done_copy]

        if canceled:
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + " canceled " + str(canceled) + " blocks")

    def get_priority_timeout(self, priority):
        if priority >= 100:
            return 5000
        if priority >= 95:
            return 10000
        return 20000

    def has_interesting_pieces(self):
        if self.peer.bitfield is None or self.peer.bitfield.has_none:
            return False

        return self.peer.torrent.data_manager.bitfield.interested_in(self.peer.bitfield)

    def request_rejected(self, piece_index, offset, length):
        with self.lock:
            peer_download = [x for x in self.downloading if x[0].piece_index == piece_index and x[0].start_byte_in_piece == offset]
            if len(peer_download) != 0:
                peer_download[0][0].remove_downloader(self.peer)
                Logger().write(LogVerbosity.Debug, "Removed a rejected request from peer download manager")
                self.downloading.remove(peer_download[0])

    def log(self):
        cur_downloading = [str(block.index) + ", " for block, request_time in self.downloading]
        Logger().write(LogVerbosity.Important, "       Currently downloading: " + str(len(self.downloading)))
        Logger().write(LogVerbosity.Important, "       Blocks: " + ''.join(str(e) for e in cur_downloading))
        Logger().write(LogVerbosity.Important, "       Done blocks: " + ','.join(str(x) for x in self.blocks_done))
        Logger().write(LogVerbosity.Important, "       Speed: " + write_size(self.peer.counter.value))

    def stop(self):
        self.stopped = True
        with self.lock:
            for block, request_time in self.downloading:
                block.remove_downloader(self.peer)
            self.downloading.clear()
            self.blocks_done.clear()

