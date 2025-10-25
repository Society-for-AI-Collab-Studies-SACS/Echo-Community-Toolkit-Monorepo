"""Circuit breaker implementation used by the enhanced dispatcher."""

from __future__ import annotations

import time
from enum import Enum
from typing import Optional

import logging

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_attempts: int = 1,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts

        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_successes = 0

    def is_open(self) -> bool:
        if self.state == CircuitState.OPEN:
            assert self.last_failure_time is not None
            if time.time() - self.last_failure_time >= self.timeout:
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.half_open_successes = 0
                return False
            return True
        return False

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_attempts:
                logger.info("Circuit breaker transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_failure_time = None
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker transitioning to OPEN (recovery failed)")
            self.state = CircuitState.OPEN
            return
        if self.failure_count >= self.failure_threshold:
            logger.warning("Circuit breaker transitioning to OPEN (threshold reached)")
            self.state = CircuitState.OPEN

    def reset(self) -> None:
        logger.info("Circuit breaker manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_successes = 0

