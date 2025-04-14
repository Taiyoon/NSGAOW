from collections import deque
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator

from loguru import logger
import simpy
from simpy.resources.container import ContainerGet

from simenv.task import CoopTask
from simenv.utils import deref
from simenv.utils.traits import DepRunnable

from .base import SchedulerBase, WorldBase, WorldElemBase

if TYPE_CHECKING:
    from simenv.task import TaskHybridBase
    from simenv.vm import VMBase, VMHybridBase
    from simenv.world import WorldHybridBase


class VMElemBase[T: WorldBase, U: 'VMBase'](  # type: ignore[type-arg]
        WorldElemBase[T], ABC):
    def __init__(self, vm: U) -> None:
        super().__init__(vm.world)
        self._vm = vm

    @property
    def vm(self) -> U:
        return deref(self._vm)


class VMSchedulerBase(VMElemBase['WorldHybridBase', 'VMHybridBase'], SchedulerBase['WorldHybridBase'], DepRunnable, ABC):
    def __init__(self, vm: 'VMHybridBase') -> None:
        super().__init__(vm)
        self._tasks: set['TaskHybridBase'] = set()
        self._task_cnt = simpy.Container(self.env)
        self.init_deprun()
        self.add_dependent(self.world.scheduler)
        # mqt stastistics
        self._last_time = self.now
        self._mqt = 0.
        self.MQT_ALPHA = 0.1  # smooth factor
        self.DELTA_TIME = self.world.DELTA_TIME

    def receive(self, task: 'TaskHybridBase') -> None:
        self._tasks.add(task)
        self._task_cnt.put(1)
        self.ctxlog.info(f"received task {task}")

    def _run_inner(self) -> Generator[simpy.Event, None, None]:
        while not self.is_all_dependent_finished:
            yield self._task_cnt.get(1)
            task = self._next_task()
            self._tasks.remove(task)
            yield from self._schedule(task)

    @property
    def mqt(self) -> float:
        return self._mqt

    def _schedule(self, task: 'TaskHybridBase') -> Generator[simpy.Event, None, None]:
        'ensure vm received a working state task'

        if task.state != task.State.RUNNING:
            task.run()
        if isinstance(task, CoopTask):
            enqueue_time = self.now

            def callback(e: simpy.Event) -> None:
                task.request_complete()
                alpha = self.MQT_ALPHA
                now = self.now
                self._mqt = (1-alpha) ** ((now - self._last_time) / self.DELTA_TIME)\
                    * self._mqt + alpha * (now - enqueue_time)
                self._last_time = self.now
            while task.current_request.location != self.vm.location:
                yield task.last_req_finish
            if task.swap_times_left > 2:
                # task.last_req_finish.callbacks.append(
                    # lambda e: self.receive(task))
                    # FIXME
                    raise NotImplementedError
            proc = self.env.process(self.vm.process(
                task.current_request.data, task.current_request.cycle))
            proc.callbacks.append(callback)
        else:
            raise NotImplementedError(
                f"Task type {type(task)} not supported")

    @abstractmethod
    def _next_task(self) -> 'TaskHybridBase':
        ...


class VMSchedulerFIFO(VMSchedulerBase):
    def __init__(self, vm: 'VMHybridBase') -> None:
        super().__init__(vm)
        self._fifo_queue: deque['TaskHybridBase'] = deque()

    def receive(self, task: 'TaskHybridBase') -> None:
        self._fifo_queue.append(task)
        super().receive(task)

    def _next_task(self) -> 'TaskHybridBase':
        return self._fifo_queue.popleft()
