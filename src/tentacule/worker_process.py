import signal
from multiprocessing import Queue, Process
from queue import Empty
from threading import Event
from types import GeneratorType
from typing import Callable

import dill

from tentacule.i_worker_process import IWorkerProcess


# Satellite value to detect the end of a generator
class GeneratorEnd:
    pass


class SimpleWorkerProcess(IWorkerProcess):
    def __init__(self, task_queue: Queue, result_queue: Queue, daemon: bool = True):
        self.native_process = Process(target=self.worker_target, daemon=daemon)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def start(self):
        self.native_process.start()

    def worker_target(self):
        sigtermd: Event = Event()
        signal.signal(signal.SIGINT, lambda *args: sigtermd.set())
        signal.signal(signal.SIGTERM, lambda *args: sigtermd.set())

        while not sigtermd.is_set():
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

        if isinstance(result, GeneratorType):
            for sub_result in result:
                self.result_queue.put((task_id, sub_result, True))

            self.result_queue.put((task_id, GeneratorEnd, True))
            return  # End

        self.result_queue.put((task_id, result, False))
