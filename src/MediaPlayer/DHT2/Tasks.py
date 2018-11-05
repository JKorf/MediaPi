from MediaPlayer.DHT2.Messages import QueryDHTMessage
from MediaPlayer.DHT2.Util import DHTTaskState
from Shared.Logger import Logger


class BaseTask:

    def __init__(self, dht_engine, on_complete):
        self.dht_engine = dht_engine
        self.on_complete = on_complete
        self.complete_on_no_requests = False

        self.outstanding_requests = 0
        self.state = DHTTaskState.Initial

    def execute(self):
        self.state = DHTTaskState.Running
        self.execute_internal()

    def send_request(self, msg, expecting_response_type, ip, port, on_response, on_timeout):
        self.outstanding_requests += 1
        self.dht_engine.socket.send_message(msg,
                                            expecting_response_type,
                                            ip,
                                            port,
                                            lambda data: self.on_response_internal(on_response, data),
                                            lambda: self.on_response_timeout(on_timeout))

    def on_response_internal(self, handler, data):
        self.outstanding_requests -= 1
        handler(data)

        if self.outstanding_requests == 0 and self.complete_on_no_requests:
            self.on_complete()
            self.state = DHTTaskState.Done

    def on_response_timeout(self, handler):
        self.outstanding_requests -= 1
        handler()

        if self.outstanding_requests == 0 and self.complete_on_no_requests:
            self.on_complete()
            self.state = DHTTaskState.Done


class FindNodeTask(BaseTask):

    def __init__(self, dht_engine, node_id, target, on_complete):
        super().__init__(dht_engine, on_complete)
        self.node_id = node_id
        self.target = target

    def execute_internal(self):
        self.complete_on_no_requests = True
        request = QueryDHTMessage.create_find_node(self.node_id, self.target)
        self.send_request(request,
                          "r",
                          self.dht_engine.routing_table.buckets[0].nodes[0].ip,
                          self.dht_engine.routing_table.buckets[0].nodes[0].port,
                          self.initialize_response,
                          self.initialize_timeout)

    def initialize_response(self, data):
        Logger.write(2, "Initialize request got a response: " + str(data))

    def initialize_timeout(self):
        Logger.write(2, "Initialize request timed out")