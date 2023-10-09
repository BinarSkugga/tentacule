import signal
from multiprocessing import Queue, Process
from typing import Callable

import dill

from i_worker_process import IWorkerProcess


class SimpleWorkerProcess(IWorkerProcess):
    def __init__(self, task_queue: Queue, result_queue: Queue, daemon: bool = True):
        self.native_process = Process(target=self.worker_target, daemon=daemon)
        self.task_queue = task_queue
        self.result_queue = result_queue

        self.sigtermd = False

    def start(self):
        self.native_process.start()

    def worker_target(self):
        signal.signal(signal.SIGINT, self.stop_worker)
        signal.signal(signal.SIGTERM, self.stop_worker)

        while not self.sigtermd:
            task_id, task, args, kwargs = self.task_queue.get()

            self._target_wrapper(task_id, dill.loads(task), *args, **kwargs)

    def _target_wrapper(self, task_id: str, target: Callable, *args, **kwargs):
        try:
            result = target(*args, **kwargs)
        except Exception as e:
            result = e

        self.result_queue.put((task_id, result))

    def stop_worker(self):
        self.sigtermd = True
