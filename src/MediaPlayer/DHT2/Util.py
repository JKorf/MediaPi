from threading import Lock

from MediaPlayer.Util.Bencode import bencode


class TransactionIdManager:
    current_id = bytearray(2)
    lock = Lock()

    @staticmethod
    def next_trans_id():
        with TransactionIdManager.lock:

            result = bytes(TransactionIdManager.current_id)
            if TransactionIdManager.current_id[0] < 255:
                TransactionIdManager.current_id[0] += 1
            elif TransactionIdManager.current_id[1] < 255:
                TransactionIdManager.current_id[1] += 1
            else:
                TransactionIdManager.current_id = bytearray(2)
        return bencode(bytes(result))


class DHTTaskState:
    Initial = 0,
    Running = 1,
    Done = 2