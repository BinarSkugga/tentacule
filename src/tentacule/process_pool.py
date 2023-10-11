import time
from multiprocessing import Queue
from queue import Empty
from threading import Thread
from types import GeneratorType
from typing import Any, Type, List, Callable, Optional

import dill

from tentacule.i_process_pool import IProcessPool
from tentacule.i_worker_process import IWorkerProcess
from tentacule.result_event import ResultEvent
from tentacule.utils import terminate_process_with_timeout, generate_unique_id
from tentacule.worker_process import SimpleWorkerProcess, GeneratorEnd


STOP_ID = '__STOP__'


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
            _ = [p.native_process.kill() for p in self._pool]
        else:
            for process in self._pool:
                terminate_process_with_timeout(process.native_process, self.terminate_timeout)

        self._result_queue.put((STOP_ID, None, False))  # Prevents having to wait the result_timeout when we shutdown
        self._stop_pool = True
        self._result_thread.join()

    def submit(self, task: Callable, *args, **kwargs) -> str:
        task_id = generate_unique_id()

        self._results[task_id] = [ResultEvent()]
        self._task_queue.put((task_id, dill.dumps(task), args, kwargs))

        return task_id

    def fetch(self, task_id: str, timeout: int = 30) -> Any:
        result = self._results[task_id][-1].result(timeout)
        return result[0]

    def stream(self, task_id: str, timeout: int = 30) -> GeneratorType:
        last_idx = 0
        while True:
            events = self._results[task_id]
            next_event = events[last_idx] if last_idx < len(events) else None
            if next_event is None:
                time.sleep(.001)
                continue

            next_result = next_event.result(timeout)[0]
            if next_result == GeneratorEnd:
                return

            last_idx += 1
            yield next_result

    def submit_and_fetch(self, task: Callable, *args, timeout: int = 30, **kwargs) -> Any:
        task_id = self.submit(task, *args, **kwargs)
        return self.fetch(task_id, timeout)

    def submit_and_stream(self, task: Callable, *args, timeout: int = 30, **kwargs) -> GeneratorType:
        task_id = self.submit(task, *args, **kwargs)
        return self.stream(task_id, timeout)

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
                task_id, result, is_generator = self._result_queue.get(timeout=self.result_timeout)
                if task_id == STOP_ID:
                    break

                self._results[task_id][-1].set_result((result, time.monotonic()))

                self._rebalance()
                self._results = {
                    k: v for k, v in self._results.items()
                    if not v[-1].is_set() or time.monotonic() - v[-1]._result[1] < self.result_timeout
                }

                if is_generator:
                    self._results[task_id].append(ResultEvent())
            except Empty:
                pass  # It's okay if the queue was empty, just retry to get
