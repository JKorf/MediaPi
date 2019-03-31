from MediaPlayer.TorrentStreaming.Peer.PeerMessages import RequestMessage, CancelMessage
from MediaPlayer.Util.Enums import PeerInterestedState, PeerChokeState, PeerState, PeerSpeed
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Util import current_time, write_size


class PeerDownloadManager(LogObject):
    @property
    def max_blocks(self):
        if self.peer.peer_speed != PeerSpeed.Low:
            return self._fast_peer_max_blocks
        return self._low_peer_max_blocks
        # if self.peer.round_trip_average != 0:
        #     single_block_speed = self._block_size * (1000 / self.peer.round_trip_average)
        #     target = self.peer.counter.value * 1.5
        #     blocks = target // single_block_speed
        #     blocks = max(self._low_peer_max_blocks, blocks)
        #     blocks = min(self._fast_peer_max_blocks, blocks)
        # self.peer.max_blocks_log = blocks
        # return blocks

    def __init__(self, peer):
        super().__init__(peer, "download")

        self.peer = peer
        self.stopped = False
        self.downloading = []
        self.blocks_done = []

        self._block_size = Settings.get_int("block_size")
        self._low_peer_max_blocks = Settings.get_int("low_peer_max_download_buffer") // self._block_size
        self._medium_peer_max_blocks = Settings.get_int("medium_peer_max_download_buffer") // self._block_size
        self._fast_peer_max_blocks = Settings.get_int("fast_peer_max_download_buffer") // self._block_size

        self.timed_out_blocks = 0

        # Logging props
        self.downloading_log = ""

    def update(self):
        if self.peer.state != PeerState.Started:
            return True

        self.check_done_blocks()
        self.check_timeout_blocks()

        if self.peer.communication_state.out_interest == PeerInterestedState.Uninterested:
            return True

        if len(self.downloading) >= self.max_blocks:
            return True

        if self.peer.communication_state.in_choke == PeerChokeState.Choked:
            #if len(self.peer.allowed_fast_pieces) == 0:
            return True

            # with self.lock:
            #     new_blocks = self.max_blocks - len(self.downloading)
            #     to_download = self.peer.torrent.download_manager.get_allowed_fast_blocks_to_download(self.peer, new_blocks)
            #     for block in to_download:
            #         self.downloading.append((block, current_time()))
            #
            #     if len(to_download) == 0:
            #         return True
            #
            #     Logger().write(LogVerbosity.Debug, str(self.peer.id) + " requesting " + str(len(to_download)) + " allowed fast blocks")
            #     self.request(to_download)
            #     return True

        if current_time() - self.timed_out_blocks < 5000:
            # We have timed out on block we previously requested, don't request new for some time
            return True

        new_blocks = self.max_blocks - len(self.downloading)
        to_download = self.peer.torrent.download_manager.get_blocks_to_download(self.peer, new_blocks)
        self.downloading += [(block, current_time()) for block in to_download]
        self.request(to_download)
        return True

    def request(self, to_download):
        download_count = len(to_download)
        if download_count > 0:
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + " going to request " + str(len(to_download)) + " blocks")
            self.peer.protocol_logger.update("Sending requests", True)
        for block in to_download:
            block.add_downloader(self.peer)
            request = RequestMessage(block.piece_index, block.start_byte_in_piece, block.length)
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Sending request for piece ' + str(request.index) + ", block " + str(
                request.offset // 16384))
            self.peer.connection_manager.send(request.to_bytes())
        self.downloading_log = ", ".join([str(x[0].index) for x in self.downloading])

    def block_done(self, block_offset, timestamp):
        self.blocks_done.append((block_offset, timestamp))

    def check_done_blocks(self):
        for block_offset, timestamp in self.blocks_done:
            downloading_block = [(block, request_time) for block, request_time in self.downloading if block.start_byte_total == block_offset]
            if len(downloading_block) == 0:
                continue  # Not currently registered as downloading

            downloading_block = downloading_block[0]
            round_trip_time = timestamp - downloading_block[1]
            self.peer.adjust_round_trip_time(round_trip_time)
            self.downloading.remove(downloading_block)
            self.downloading_log = ", ".join([str(x[0].index) for x in self.downloading])
            downloading_block[0].remove_downloader(self.peer)
        self.blocks_done.clear()

    def check_timeout_blocks(self):
        canceled = 0

        timed_out_blocks = [(block, request_time) for block, request_time in self.downloading
                            if current_time() - request_time > self.get_priority_timeout(self.peer.torrent.data_manager._pieces[block.piece_index].priority)]

        for block_request in timed_out_blocks:
            block = block_request[0]
            self.downloading.remove(block_request)
            self.downloading_log = ", ".join([str(x[0].index) for x in self.downloading])

            cancel_msg = CancelMessage(block.piece_index, block.start_byte_in_piece, block.length)
            self.peer.protocol_logger.update("Sending cancel (timeout)")
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Sending cancel for piece ' + str(block.piece_index) + ", block " + str(cancel_msg.offset // 16384))
            self.peer.connection_manager.send(cancel_msg.to_bytes())

            block.remove_downloader(self.peer)
            canceled += 1

        if canceled:
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + " canceled " + str(canceled) + " blocks")
            self.timed_out_blocks = current_time()

    @staticmethod
    def get_priority_timeout(priority):
        if priority >= 100:
            return 5000
        if priority >= 95:
            return 15000
        return 9999999999

    def has_interesting_pieces(self):
        if self.peer.bitfield is None or self.peer.bitfield.has_none:
            return False

        return self.peer.torrent.data_manager.bitfield.interested_in(self.peer.bitfield)

    def request_rejected(self, piece_index, offset, length):
        peer_download = [x for x in self.downloading if x[0].piece_index == piece_index and x[0].start_byte_in_piece == offset]
        if len(peer_download) != 0:
            peer_download[0][0].remove_downloader(self.peer)
            Logger().write(LogVerbosity.Debug, "Removed a rejected request from peer download manager")
            self.downloading.remove(peer_download[0])
            self.downloading_log = ", ".join([str(x[0].index) for x in self.downloading])
            self.timed_out_blocks = current_time()

    def log(self):
        cur_downloading = [str(block.index) + ", " for block, request_time in self.downloading]
        Logger().write(LogVerbosity.Important, "       Currently downloading: " + str(len(self.downloading)))
        Logger().write(LogVerbosity.Important, "       Blocks: " + ''.join(str(e) for e in cur_downloading))
        Logger().write(LogVerbosity.Important, "       Done blocks: " + ','.join(str(x) for x in self.blocks_done))
        Logger().write(LogVerbosity.Important, "       Speed: " + write_size(self.peer.counter.value))

    def stop(self):
        self.stopped = True
        for block, request_time in self.downloading:
            block.remove_downloader(self.peer)
        self.downloading.clear()
        self.blocks_done.clear()
        self.downloading_log = ""

