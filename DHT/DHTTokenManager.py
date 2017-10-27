import hashlib
import os
from threading import Lock

from Shared.Util import current_time
from TorrentSrc.Util.Bencode import bencode


class TransactionIdManager:
    current_id = bytearray(2)
    lock = Lock()

    @staticmethod
    def next_trans_id():
        TransactionIdManager.lock.acquire()

        result = bytes(TransactionIdManager.current_id)
        if TransactionIdManager.current_id[0] < 255:
            TransactionIdManager.current_id[0] += 1
        elif TransactionIdManager.current_id[1] < 255:
            TransactionIdManager.current_id[1] += 1
        else:
            TransactionIdManager.current_id = bytearray(2)
        TransactionIdManager.lock.release()
        return bencode(bytes(result))


class TokenManager:

    secret = bytes(10)
    previous_secret = bytes(10)
    last_generated = 0

    @staticmethod
    def init():
        TokenManager.secret = os.urandom(10)
        TokenManager.previous_secret = os.urandom(10)
        TokenManager.last_generated = current_time()

    @staticmethod
    def generate_token(node):
        return TokenManager.get_token(node, TokenManager.secret)

    @staticmethod
    def verify_token(node, token):
        return TokenManager.token_equals(token, TokenManager.get_token(node, TokenManager.secret)) or TokenManager.token_equals(token, TokenManager.get_token(node, TokenManager.previous_secret))

    @staticmethod
    def token_equals(token1, token2):
        for i in range(len(token1)):
            if token1[i] != token2[i]:
                return False
        return True

    @staticmethod
    def get_token(node, bytes):
        if current_time() - TokenManager.last_generated > 5 * 60 * 1000:
            TokenManager.last_generated = current_time()
            TokenManager.previous_secret = TokenManager.secret
            TokenManager.secret = os.urandom(10)

        copy = bytearray(bytes)
        node_bytes = node.ip_port_bytes()
        for i in range(len(node_bytes)):
            copy[i] |= node_bytes[i]
        return hashlib.sha1(copy).digest()

