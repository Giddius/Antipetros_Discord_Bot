from abc import ABC, abstractmethod
import asyncio
from typing import Callable


class AbstractConnectSignal(ABC):

    def __init__(self) -> None:
        self.targets = set()

    def connect(self, target: Callable):
        self.targets.add(target)

    @abstractmethod
    async def emit(self, *args, **kwargs):
        # IDEA maybe as asyncio.task
        await self._emit_to_targets(*args, **kwargs)

    async def _emit_to_targets(self, *args, **kwargs):
        for target in self.targets:
            if asyncio.iscoroutinefunction(target):
                await target(*args, **kwargs)
            else:
                target(*args, **kwargs)
