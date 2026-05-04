import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from botgateway.core.router import CooldownTracker
from botgateway.db import ModelGroup


@dataclass
class RetryConfig:
    retry_count: int = 3
    retry_delay: float = 1.0
    cooldown_period: int = 60
    exponential_backoff: bool = False


class ErrorRetryHandler:
    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self.cooldown_tracker = CooldownTracker()
        self._retry_counts: dict[str, int] = {}

    def record_error(self, model_id: str) -> None:
        self._retry_counts[model_id] = self._retry_counts.get(model_id, 0) + 1
        self.cooldown_tracker.record_error(model_id, time.time())

    def should_retry(self, model_id: str) -> bool:
        retry_count = self._retry_counts.get(model_id, 0)
        return retry_count < self.config.retry_count

    def get_retry_delay(self, attempt: int) -> float:
        if self.config.exponential_backoff:
            return self.config.retry_delay * (2 ** attempt)
        return self.config.retry_delay

    def reset(self, model_id: str | None = None) -> None:
        if model_id:
            self._retry_counts.pop(model_id, None)
            self.cooldown_tracker.clear(model_id)
        else:
            self._retry_counts.clear()
            self.cooldown_tracker.clear()

    @classmethod
    def from_model_group(cls, group: ModelGroup) -> "ErrorRetryHandler":
        config = RetryConfig(
            retry_count=group.retry_count,
            retry_delay=group.retry_delay,
            cooldown_period=group.cooldown_period,
        )
        return cls(config)


class RetryExecutor:
    def __init__(self, handler: ErrorRetryHandler):
        self.handler = handler

    # UNCOVERED: 需要模拟外部 API 调用，集成测试覆盖
    async def execute_with_retry(
        self,
        model_id: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        last_error = None

        for attempt in range(self.handler.config.retry_count + 1):
            try:
                result = await func(*args, **kwargs)
                self.handler.reset(model_id)
                return result
            except Exception as e:
                last_error = e
                self.handler.record_error(model_id)

                # UNCOVERED: asyncio.sleep 在测试中使用 mock
                if attempt < self.handler.config.retry_count:
                    delay = self.handler.get_retry_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    break

        raise last_error
