from typing import Dict, List, Any
from copy import deepcopy
from collections import defaultdict
import time
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor, Future

from app.utils import current_timestamp


executor = ThreadPoolExecutor(max_workers=5)


class TimedList:

    _create_at: int
    _list_: List[Any]

    def __init__(self):
        self._create_at = current_timestamp()
        self._list_ = []

    def append(self, element, *, delay: int = 3):
        self._list_.append(element)
        self._create_at += delay * 1000

    def clear(self) -> List[Any]:
        if self._create_at < current_timestamp():
            pop_list = self._list_
            self._list_ = []
            self._create_at = current_timestamp()
            return pop_list
        return []



class MessageReceiveQueue:

    lock = Lock() # 反正单机的，简单标志就行
    session_id_to_msgs : Dict[str, TimedList] = defaultdict(TimedList)

    def send(self, session_id, msg, delay=3):
        if session_id not in self.session_id_to_msgs:
            with self.lock:
                self.session_id_to_msgs[session_id].append(msg, delay=delay)
        self.session_id_to_msgs[session_id].append(msg, delay=delay)

    def _proceed(self):
        from app.service.chatflow import chat

        while True:
            with self.lock:
                futures = []
                for session_id, tls_ in self.session_id_to_msgs.items():
                    msgs = tls_.clear()
                    if len(msgs) > 0:
                        # futures.append(executor.submit(chat, msgs))
                        chat(msgs)
                # for f in futures:
                #     f.result()
            time.sleep(0.1)


class MessageReplyQueue:

    lock = Lock()
    session_id_to_msgs : Dict[str, List[str]] = defaultdict(list)

    def send(self, session_id, msg_id):
        if session_id not in self.session_id_to_msgs:
            with self.lock:
                self.session_id_to_msgs[session_id].append(msg_id)
        self.session_id_to_msgs[session_id].append(msg_id)

    def _proceed(self):
        from app.service.chatflow import reply

        while True:
            with self.lock:
                for session_id, msg_ids in self.session_id_to_msgs.items():
                    if len(msg_ids) > 0:
                        msg_id = msg_ids.pop()
                        reply(msg_id)
            time.sleep(0.1)


message_receive_queue = MessageReceiveQueue()
_thread0 = Thread(name="message_queue_thread", target=message_receive_queue._proceed).start()


message_reply_queue = MessageReplyQueue()
_thread1 = Thread(name="message_reply_thread", target=message_reply_queue._proceed).start()
