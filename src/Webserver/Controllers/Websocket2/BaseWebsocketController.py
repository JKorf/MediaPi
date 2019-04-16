from flask_socketio import Namespace

from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread
from Webserver.APIController import APIController, Request


class BaseWebsocketController(Namespace):

    def __init__(self, namespace):
        super().__init__(namespace)
        self.requests = []

    def request_wait(self, topic, timeout, room, *args):
        request_message = self._send_request(topic, args, room)
        return self.wait_for_request_response(request_message, timeout)

    def request_cb(self, topic, callback, timeout, room, *args):
        request_message = self._send_request(topic, args, room)
        thread = CustomThread(self.wait_for_request_response, "Request callback " + topic, [request_message, timeout, callback])
        thread.start()

    def send_no_wait(self, topic, command, room, args):
        Logger().write(LogVerbosity.Debug, "Client command: " + topic + ", command")
        self.emit("command", (topic, command, *args), room=room)

    def on_response(self, request_id, *args):
        Logger().write(LogVerbosity.Debug, "Client response for id " + str(request_id) + ": " + str(args))
        requests = [x for x in self.requests if x.request_id == request_id]
        if len(requests) == 0:
            Logger().write(LogVerbosity.Debug, "No pending request found for id " + str(request_id))
            return

        requests[0].set(args)

    def _send_request(self, topic, data, room):
        Logger().write(LogVerbosity.Debug, "Sending request: " + topic + ", data: " + str(data))
        request_id = APIController().next_id()
        request_message = Request(request_id, topic, data, room, self._complete_request)
        self.requests.append(request_message)
        self.emit("request", (request_id, topic, data), room=room)
        return request_message

    def timeout_request(self, request_message):
        self.emit("timeout", request_message.request_id, room=request_message.room)

    def wait_for_request_response(self, request_message, timeout, callback=None):
        responded, response = request_message.wait(timeout)
        if not responded:
            self.timeout_request(request_message)
            response = [None]

        if callback is not None:
            callback(*response)
        return response

    def _complete_request(self, request_message):
        self.requests.remove(request_message)
        Logger().write(LogVerbosity.Debug, "Request done, now " + str(len(self.requests)) + " requests open")
