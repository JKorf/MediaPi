from threading import Lock

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time
from MediaPlayer.Peer.PeerMessages import RequestMessage
from MediaPlayer.Util.Enums import ConnectionState, PeerSpeed, PeerInterestedState, PeerChokeState


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

        if self.peer.communication_state.in_choke == PeerChokeState.Choked:
            return True

        if self.peer.communication_state.out_interest == PeerInterestedState.Uninterested:
            return True

        if len(self.downloading) >= self.max_blocks:
            return True

        with self.lock:
            if self.stopped:
                return False

            new_blocks = self.max_blocks - len(self.downloading)
            to_download = self.get_next_blocks_to_download(new_blocks)
            for block_download in to_download:
                request = RequestMessage(block_download.block.piece_index, block_download.block.start_byte_in_piece, block_download.block.length)
                Logger.write(1, str(self.peer.id) + ' Sending request for piece ' + str(request.index) + ", block " + str(
                    request.offset // 16384))
                self.peer.torrent.outstanding_requests += 1
                self.peer.connection_manager.send(request.to_bytes())

        return True

    def check_current_downloading(self):
        canceled = 0

        with self.lock:
            for peer_download in list(self.downloading):
                if peer_download.block_download.block.done:
                    # Block already done
                    self.downloading.remove(peer_download)
                    peer_download.block_download.remove_peer(self.peer)
                    continue

                prio_timeout = 0
                if self.peer.peer_speed == PeerSpeed.Low and self.peer.torrent.peer_manager.are_fast_peers_available():
                    prio_timeout = (peer_download.block_download.piece.priority / 2) * 1000

                passed_time = current_time() - peer_download.request_time
                if passed_time > (55000 - prio_timeout):
                    self.downloading.remove(peer_download)
                    peer_download.block_download.remove_peer(self.peer)
                    canceled += 1
        if canceled:
            Logger.write(1, "Canceled " + str(canceled))

    def get_next_blocks_to_download(self, amount):
        blocks_to_download = self.peer.torrent.download_manager.get_blocks_to_download(self.peer, amount)
        for block in blocks_to_download:
            self.downloading.append(PeerDownload(block))

        return blocks_to_download

    def has_interesting_pieces(self):
        if self.peer.bitfield is None or self.peer.bitfield.has_none:
            return False

        return self.peer.torrent.data_manager.bitfield.interested_in(self.peer.bitfield)

    def request_rejected(self, piece_index, offset, length):
        with self.lock:
            block = self.peer.torrent.data_manager.get_block_by_offset(piece_index, offset)
            peer_download = [x for x in self.downloading if x.block_download.block.index == block.index]
            if len(peer_download) != 0:
                peer_download[0].block_download.remove_peer(self.peer)
                Logger.write(1, "Removed a rejected request from peer download manager")
                self.downloading.remove(peer_download[0])

    def log(self):
        Logger.write(3, "       Currently downloading: " + str(len(self.downloading)))
        Logger.write(3, "       Speed: " + str(self.peer.counter.value))

    def stop(self):
        self.stopped = True
        with self.lock:
            for peer_download in self.downloading:
                peer_download.block_download.remove_peer(self.peer)
            self.downloading.clear()


class PeerDownload:

    def __init__(self, block_download):
        self.block_download = block_download
        self.request_time = current_time()

