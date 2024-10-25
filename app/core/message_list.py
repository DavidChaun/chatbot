import threading
import queue
import time


class AutoDestroyQueue:
    def __init__(self, scan_interval=5, destroy_timeout=3600):
        self.msgs = []
        self.queue = queue.Queue()
        self.scan_interval = scan_interval
        self.destroy_timeout = destroy_timeout
        self.last_push_time = time.time()
        self.running = True

        self.scan_thread = threading.Thread(target=self.scan_queue)
        self.destroy_thread = threading.Thread(target=self.destroy_queue)

        self.scan_thread.start()
        self.destroy_thread.start()

    def push(self, item):
        self.queue.put(item)
        self.last_push_time = time.time()

    def consume(self):
        while not self.queue.empty():
            item = self.queue.get()
            print(f"Consumed: {item}")
            self.queue.task_done()

    def scan_queue(self):
        while self.running:
            time.sleep(self.scan_interval)
            if not self.queue.empty():
                self.consume()

    def destroy_queue(self):
        while self.running:
            time.sleep(1)
            if time.time() - self.last_push_time >= self.destroy_timeout:
                if not self.queue.empty():
                    self.consume()
                self.running = False
        self.stop()

    def stop(self):
        self.scan_thread.join()
        self.destroy_thread.join()

