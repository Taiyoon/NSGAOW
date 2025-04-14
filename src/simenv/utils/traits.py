from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from functools import cache, cached_property, partial
from typing import (TYPE_CHECKING, Any, Callable, Dict, Generator, List, Protocol, Self, Set,
                    final)

import loguru
import simpy
from loguru import logger

if TYPE_CHECKING:
    from simenv.base import Base, WorldBase, WorldElemBase


class Loggable(Protocol):
    """
    A mixin class that provides log functionality to the class it is mixed into.
    """
    const_context: Dict[str, Any]
    eval_context: Dict[str, Callable[[Any], Any]]

    @property
    def ctxlog(self) -> loguru.Logger:
        return self._const_context_logger.bind(**{k: v(self) for k, v in self.eval_context.items()})

    @property
    def _const_context_logger(self) -> loguru.Logger:
        return logger.bind(name=str(self), **self.const_context)


class Presistable(Protocol):
    pass


class Runnable(Protocol):
    class RunState(Enum):
        INIT = auto()
        RUNNING = auto()
        FINISHED = auto()

    # required properties
    @property
    def env(self) -> simpy.Environment:
        ...

    # required methods
    def _run_inner(self) -> Generator[simpy.Event, None, None]:
        """
        Run method of runnable elements

        This method should be implemented by all runnable elements. It should only yield
        simpy.events. The method should not submit to this event or receive returns.

        Yields:
            Generator[simpy.Event, None, None]: simpy.events
        """
        ...

    # provided property
    _run_state: RunState
    _finish_event: simpy.Event

    def init_run(self) -> None:
        self._run_state = self.RunState.INIT
        self._finish_event = simpy.Event(self.env)

    def _before_run(self) -> None:
        if self._run_state != self.RunState.INIT:
            raise RuntimeError('Cannot rerun a runnable element')
        self._run_state = self.RunState.RUNNING

    def add_finish_callback(self, callback: Callable[[simpy.Event], None]) -> None:
        self._finish_event.callbacks.append(callback)

    def _after_run(self) -> None:
        self._run_state = self.RunState.FINISHED
        self._finish_event.succeed()

    def run(self) -> simpy.Process:
        self._before_run()
        proc = self.env.process(self._run_inner())
        proc.callbacks.append(self._after_run())
        return proc

    @property
    def is_finished(self) -> bool:
        return self._run_state == self.RunState.FINISHED

    @property
    def is_running(self) -> bool:
        return self._run_state == self.RunState.RUNNING


class DepRunnable(Runnable, Protocol):
    _depedent: Set[Runnable]

    def init_run(self) -> None:
        raise RuntimeError(
            'DependentRunnable cannot be initialized by init_run')

    def init_deprun(self) -> None:
        super().init_run()
        self._depedent = set()

    def add_dependent(self, runnable: Runnable) -> None:
        self._depedent.add(runnable)
        self.add_finish_callback(partial(self._depedent.remove, runnable))

    @property
    def is_all_dependent_finished(self) -> bool:
        return len(self._depedent) == 0

    @property
    def dependent_runnables(self) -> Generator[simpy.Event, None, None]:
        return (r._finish_event for r in self._depedent)
