import time
from multiprocessing import Queue
from threading import Thread
from time import sleep
from typing import Any, Type, List, Callable, Optional

import dill

from i_process_pool import IProcessPool
from i_worker_process import IWorkerProcess
from utils import terminate_process_with_timeout, generate_unique_id
from worker_process import SimpleWorkerProcess


class ProcessPool(IProcessPool):
    def __init__(self, workers: int, worker_class: Type[IWorkerProcess] = SimpleWorkerProcess):
        self.workers = workers
        self.worker_class = worker_class

        self.terminate_timeout = 5
        self._pool: List[IWorkerProcess] = []
        self._stop_pool = False

        self._task_queue = Queue()
        self._result_queue = Queue()

        self.result_timeout = 30
        self._results = {}
        self._result_thread: Optional[Thread] = Thread(target=self._watch_for_result, daemon=True)

    def start(self):
        self._pool = [
            SimpleWorkerProcess(self._task_queue, self._result_queue)
            for i in range(self.workers)
        ]

        self._result_thread.start()
        _ = [p.start() for p in self._pool]

    def close(self, force: bool = False):
        if force:
            self._stop_pool = True
            _ = [p.native_process.kill() for p in self._pool]
            self._result_thread.join()
            return

        for process in self._pool:
            terminate_process_with_timeout(process.native_process, self.terminate_timeout)

    def new_task(self, task: Callable, *args, **kwargs) -> str:
        task_id = generate_unique_id()
        self._task_queue.put((task_id, dill.dumps(task), args, kwargs))

        return task_id

    def get_result(self, task_id: str, timeout: int = 30) -> Any:
        t = time.monotonic()
        while time.monotonic() - t < timeout:
            try:
                result, t = self._results[task_id]
                return result
            except KeyError:
                sleep(.1)

    def _rebalance(self):
        self._pool = [p for p in self._pool if p.native_process.is_alive()]
        if self.workers == len(self._pool):
            return

        for i in range(self.workers - len(self._pool)):
            process = SimpleWorkerProcess(self._task_queue, self._result_queue)
            self._pool.append(process)

            process.start()

    def _watch_for_result(self):
        while not self._stop_pool:
            task_id, result = self._result_queue.get(timeout=self.result_timeout)
            self._results[task_id] = (result, time.monotonic())

            self._rebalance()
            self._results = {
                k: v for k, v in self._results.items()
                if time.monotonic() - v[1] < self.result_timeout
            }
