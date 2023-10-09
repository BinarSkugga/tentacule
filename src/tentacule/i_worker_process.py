from abc import ABC, abstractmethod
from multiprocessing import Process, Queue


class IWorkerProcess(ABC):
    native_process: Process

    task_queue: Queue
    result_queue: Queue

    @abstractmethod
    def start(self):
        pass
