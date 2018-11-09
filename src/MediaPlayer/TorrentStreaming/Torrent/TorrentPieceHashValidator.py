import hashlib


class TorrentPieceHashValidator:
    def __init__(self):
        self.hashes = []
        self.pieces_to_hash = []
        self.on_piece_accept = None
        self.on_piece_reject = None

    def update_hashes(self, hash_string):
        for i in range(len(hash_string) // 20):
            self.hashes.append(hash_string[i * 20: (i + 1) * 20])

    def add_piece_to_hash(self, piece):
        self.pieces_to_hash.append(piece)

    def update(self):
        for piece in list(self.pieces_to_hash):
            if not self.validate_piece(piece):
                self.on_piece_reject(piece)
            else:
                self.on_piece_accept(piece)

            self.pieces_to_hash.remove(piece)
        return True

    def validate_piece(self, piece):
        expected_hash = self.hashes[piece.index]
        data = piece.get_data()
        if not data:
            return False

        actual_hash = hashlib.sha1(data).digest()
        return expected_hash[0] == actual_hash[0] and expected_hash[8] == actual_hash[8] and expected_hash[19] == actual_hash[19]
