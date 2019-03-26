from threading import Event
from threading import Lock

from Shared.Threading import CustomThread


class MultiQueue:

    def __init__(self, name, processor):
        self.queue = []
        self.queue_lock = Lock()
        self.queue_event = Event()

        self.running = False
        self.processor = processor
        self.process_thread = CustomThread(self.process_queue, "Queue processor: " + name, [])

    def add_item(self, item):
        with self.queue_lock:
            self.queue.append(item)
            self.queue_event.set()

    def start(self):
        self.running = True
        self.process_thread.start()

    def stop(self):
        self.running = False
        self.queue_event.set()
        self.process_thread.join()

    def process_queue(self):
        while self.running:
            self.queue_event.wait(0.2)
            if not self.running:
                return

            with self.queue_lock:
                items = list(self.queue)
                self.queue.clear()
                self.queue_event.clear()

            self.processor(items)
