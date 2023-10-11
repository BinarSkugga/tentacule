from abc import ABC, abstractmethod
from types import GeneratorType
from typing import Any, Type, Callable

from tentacule.i_worker_process import IWorkerProcess


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
    def submit(self, task: Callable, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def fetch(self, task_id: str, timeout: int = 30) -> Any:
        pass

    @abstractmethod
    def stream(self, task_id: str, timeout: int = 30) -> GeneratorType:
        pass

    @abstractmethod
    def submit_and_fetch(self, task: Callable, *args, timeout: int = 30, **kwargs) -> Any:
        pass

    @abstractmethod
    def submit_and_stream(self, task: Callable, *args, timeout: int = 30, **kwargs) -> GeneratorType:
        pass
