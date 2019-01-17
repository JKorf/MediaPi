import time

from Shared.Logger import Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time


class PendingMessagesHandler:

    def __init__(self, on_added_message, on_invalid_message, on_removed_message):
        self.pending_messages = []

        self.pending_message_thread = CustomThread(self.check_pending_messages, "Check pending messages")
        self.on_invalid_message = on_invalid_message
        self.on_added_message = on_added_message
        self.on_removed_message = on_removed_message
        self.pending_message_thread.start()

    def add_pending_message(self, client_message):
        if client_message.valid_till > current_time():
            self.pending_messages.append(client_message)
        self.on_added_message(client_message)

    def check_pending_messages(self):
        while True:
            check_time = current_time()
            invalid = [x for x in self.pending_messages if x.valid_till < check_time]
            for msg in invalid:
                Logger.write(2, "Timing out message " + str(msg.id))
                self.pending_messages = [x for x in self.pending_messages if x.id != msg.id]
                self.on_invalid_message(msg)
            time.sleep(1)

    def remove_client_message(self, msg, by_client):
        self.pending_messages = [x for x in self.pending_messages if x.id != msg.id]
        self.on_removed_message(msg, by_client)

    def get_pending_for_new_client(self):
        return self.pending_messages

    def get_message_by_response_id(self, id):
        msg = [x for x in self.pending_messages if x.id == id]
        if len(msg) == 0:
            return None
        return msg[0]


class ClientMessage:

    def __init__(self, id, callback, callback_no_answer, valid_for, type, data):
        self.id = id
        self.callback = callback
        self.callback_no_answer = callback_no_answer
        self.valid_till = current_time() + valid_for
        self.type = type
        self.data = data