import signal
from multiprocessing import Queue, Process
from queue import Empty
from typing import Callable

import dill

from i_worker_process import IWorkerProcess


class SimpleWorkerProcess(IWorkerProcess):
    def __init__(self, task_queue: Queue, result_queue: Queue, daemon: bool = True):
        self.native_process = Process(target=self.worker_target, daemon=daemon)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def start(self):
        self.native_process.start()

    def worker_target(self):
        sigtermd: dict = {'close': False}

        def close(*args):
            sigtermd['close'] = True

        signal.signal(signal.SIGINT, close)
        signal.signal(signal.SIGTERM, close)

        while not sigtermd['close']:
            try:
                task_id, task, args, kwargs = self.task_queue.get(timeout=1)

                self._target_wrapper(task_id, dill.loads(task), *args, **kwargs)
            except Empty:
                pass

    def _target_wrapper(self, task_id: str, target: Callable, *args, **kwargs):
        try:
            result = target(*args, **kwargs)
        except Exception as e:
            result = e

        self.result_queue.put((task_id, result))

    def stop_worker(self, *args):
        self.sigtermd = True
