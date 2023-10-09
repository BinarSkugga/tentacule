from abc import ABC, abstractmethod
from typing import Any, Type, Callable

from i_worker_process import IWorkerProcess


class IProcessPool(ABC):
    worker_class: Type[IWorkerProcess]
    workers: int

    terminate_timeout: int
    result_timeout: int

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def close(self, force: bool):
        pass

    @abstractmethod
    def new_task(self, task: Callable, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def get_result(self, task_id: str, timeout: int = 30) -> Any:
        pass
