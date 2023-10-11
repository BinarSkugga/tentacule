from threading import Event
from typing import Any


class ResultEvent(Event):
    def __init__(self):
        super().__init__()
        self._result = None

    def set_result(self, value: Any) -> None:
        self._result = value
        super().set()

    def result(self, timeout: int = 30):
        self.wait(timeout)
        return self._result
