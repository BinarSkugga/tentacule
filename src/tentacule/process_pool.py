import time
from multiprocessing import Queue, Event
from queue import Empty
from threading import Thread
from typing import Any, Type, List, Callable, Optional

import dill

from tentacule.i_process_pool import IProcessPool
from tentacule.i_worker_process import IWorkerProcess
from tentacule.utils import terminate_process_with_timeout, generate_unique_id
from tentacule.worker_process import SimpleWorkerProcess


class ProcessPool(IProcessPool):
    def __init__(self, workers: int, worker_class: Type[IWorkerProcess] = SimpleWorkerProcess):
        self.workers = workers
        self.worker_class = worker_class

        self.terminate_timeout = 5
        self._pool: List[IWorkerProcess] = []
        self._stop_pool = False

        self._task_queue = Queue()
        self._result_queue = Queue()

        self.result_timeout = 15
        self._results = {}
        self._result_events = {}
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
        self._result_events[task_id] = Event()

        return task_id

    def get_result(self, task_id: str, timeout: int = 30) -> Any:
        try:
            self._result_events[task_id].wait(timeout)
            return self._results[task_id][0]
        finally:
            self._result_events.pop(task_id)

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
            try:
                task_id, result = self._result_queue.get(timeout=self.result_timeout)

                self._result_events[task_id].set()
                self._results[task_id] = (result, time.monotonic())

                self._rebalance()
                self._results = {
                    k: v for k, v in self._results.items()
                    if time.monotonic() - v[1] < self.result_timeout
                }
            except Empty:
                pass  # It's okay if the queue was empty, just retry to get
