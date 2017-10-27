from threading import Lock

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time
from TorrentSrc.Peer.PeerMessages import RequestMessage
from TorrentSrc.Util.Enums import ConnectionState, PeerSpeed, PeerInterestedState, PeerChokeState, TorrentState


class PeerDownloadManager:

    def __init__(self, peer):
        self.peer = peer
        self.stopped = False
        self.downloading = []
        self.lock = Lock()

        self.low_max = Settings.get_int("low_speed_max_blocks")
        self.medium_max = Settings.get_int("medium_speed_max_blocks")
        self.high_max = Settings.get_int("high_speed_max_blocks")

    def get_max_blocks(self):
        if self.peer.peer_speed == PeerSpeed.Low:
            return self.low_max
        elif self.peer.peer_speed == PeerSpeed.Medium:
            return self.medium_max
        else:
            return self.high_max

    def update(self):
        if self.peer.connection_manager.connection_state != ConnectionState.Connected:
            return True

        self.check_current_downloading()

        if not self.has_interesting_pieces():
            return True

        if self.peer.communication_state.in_choke == PeerChokeState.Choked:
            return True

        if self.peer.communication_state.out_interest == PeerInterestedState.Uninterested:
            return True

        if len(self.downloading) >= self.get_max_blocks():
            return True

        self.lock.acquire()
        if self.stopped:
            self.lock.release()
            return False

        new_blocks = self.get_max_blocks() - len(self.downloading)
        to_download = self.get_next_blocks_to_download(new_blocks)
        for block_download in to_download:
            request = RequestMessage(block_download.block.piece_index, block_download.block.start_byte_in_piece, block_download.block.length)
            Logger.write(1, str(self.peer.id) + ' Sending request for piece ' + str(request.index) + ", block " + str(
                request.offset // 16384))
            self.peer.torrent.outstanding_requests += 1
            self.peer.connection_manager.send(request.to_bytes())

        self.lock.release()

        return True

    def check_current_downloading(self):
        canceled = 0
        self.lock.acquire()

        for peer_download in list(self.downloading):
            if peer_download.block_download.block.done:
                self.downloading.remove(peer_download)
                peer_download.block_download.remove_peer(self.peer)
                continue

            if peer_download.block_download.block.piece_index < self.peer.torrent.stream_position:
                self.downloading.remove(peer_download)
                peer_download.block_download.remove_peer(self.peer)
                continue

            prio_timeout = 0
            if self.peer.peer_speed == PeerSpeed.Low and (
                    self.peer.torrent.peer_manager.medium_speed_peers > 0 or self.peer.torrent.peer_manager.high_speed_peers > 0):
                prio = self.peer.torrent.data_manager.pieces[peer_download.block_download.block.piece_index].priority
                prio_timeout = (prio / 2) * 1000

            passed_time = current_time() - peer_download.request_time
            if passed_time > (55000 - prio_timeout):
                self.downloading.remove(peer_download)
                peer_download.block_download.remove_peer(self.peer)
                canceled += 1

        self.lock.release()
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
        self.lock.acquire()
        block = self.peer.torrent.data_manager.get_block_by_offset(piece_index, offset)
        peer_download = [x for x in self.downloading if x.block_download.block.index == block.index]
        if len(peer_download) != 0:
            peer_download[0].block_download.remove_peer(self.peer)
            Logger.write(1, "Removed a rejected request from peer download manager")
            self.downloading.remove(peer_download[0])
        self.lock.release()

    def stop(self):
        self.stopped = True
        self.lock.acquire()
        for peer_download in self.downloading:
            peer_download.block_download.remove_peer(self.peer)
        self.downloading.clear()
        self.lock.release()


class PeerDownload:

    def __init__(self, block_download):
        self.block_download = block_download
        self.request_time = current_time()

