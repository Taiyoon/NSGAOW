from abc import ABC, abstractmethod
from math import isclose
from typing import TYPE_CHECKING, Generator, List, NoReturn, Set, Tuple

import numpy as np
import simpy
from simpy import Event

import simenv
from simenv.base import SchedulerBase, WorldBase
from simenv.task import CoopTask, PrivTask, TaskBase, TaskHybridBase
from simenv.utils import DepRunnable, HybridVMLocation
from simenv.vm import VMBase, VMHybridBase

if TYPE_CHECKING:
    from simenv.world import WorldHybridBase, WorldHybridOffline


class WorldSchedulerBase(SchedulerBase['WorldHybridBase'], DepRunnable, ABC):

    def _dispatch(self, task: 'TaskHybridBase', vms: Tuple['VMHybridBase', ...]) -> None:
        """
        Assign the task to the given virtual machines.

        :param vm: tuple of virtual machines
        :raises RuntimeError: if the task is not in INIT state
        :raises ValueError: if the task is dispatched to a non-proper VM
        """
        if isinstance(task, simenv.task.CoopTask):
            pass
        else:
            raise NotImplementedError(f"Task type {type(task)} not supported")
        task.vm = vms
        for vm in vms:
            vm.scheduler.receive(task)

    @property
    def rng(self) -> NoReturn:
        raise RuntimeError(
            'Scheduler should not access the main random number generator for tasks generation')

    @property
    def rng1(self) -> np.random.Generator:
        """
        A RNG that is used at random in non-task-generation cases.

        Returns:
            A numpy random number generator instance.
        """
        return self.world._rng1

    @abstractmethod
    def receive(self, task: 'TaskHybridBase') -> None:
        ...


class SchedulerOffline(WorldSchedulerBase):

    def __init__(self, world: 'WorldHybridOffline') -> None:
        super().__init__(world)
        self._tasks: List['PrivTask'] = []
        self.init_deprun()

    def _run_inner(self) -> Generator[simpy.Timeout, None, None]:
        yield self.env.timeout(0)

    def receive(self, task: 'PrivTask') -> None:  # type: ignore[override]
        self._tasks.append(task)
