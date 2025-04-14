from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Generator, List, Sequence, Tuple, Type

import numpy as np
from simpy import Event, Timeout

from simenv.base import WorldBase, WorldElemBase
from simenv.task import TaskBase
from simenv.utils.traits import Runnable

if TYPE_CHECKING:
    from simenv.world import WorldHybridOffline
    from simenv.task import TaskHybridBase
    from simenv.vm import VMBase
    from simenv.world import WorldHybridBase


class SubmitterBase[T: 'WorldBase', U: 'TaskHybridBase'](WorldElemBase[T], Runnable, ABC):

    def __init__(self, world: T):
        super().__init__(world)
        self.init_run()

    def _submit_task(self, task: U) -> None:
        self.world.scheduler.receive(task)


class SubmitterHybridDefault(SubmitterBase['WorldHybridBase', 'TaskHybridBase']):
    """
    Simple task submitter submit tasks randomlly
    """

    def __init__(self,
                 world: 'WorldHybridBase',
                 active_time: float,
                 arrival_rate: float,
                 task_types: Dict[Type['TaskHybridBase'], float]):
        """
        Initializes the TaskSubmitterHybridDefault instance.

        Args:
            world (WorldHybridBase): The world this task submitter is associated with.
            active_time (float): The time duration until the task submitter stops submitting tasks.
            arrival_rate (float): The rate at which tasks are submitted, 
                representing the average time gap between two tasks.
                in exponential distribution
            task_types (Dict[Type[HybridTaskBase], float]): A dictionary mapping from task types to their
                corresponding probabilities. The probabilities should be normalized to 1.
        """
        super().__init__(world)
        self.active_time = active_time
        self.TASK_TYPES_DICT = task_types
        task_type, prob = zip(*task_types.items())
        self.TASK_TYPES: Sequence[Type['TaskHybridBase']] = task_type
        self.TASK_TYPE_PROBS = np.array(prob, dtype=np.float64)
        # TODO: remove assert once unit test passed
        assert len(self.TASK_TYPES) == len(self.TASK_TYPE_PROBS) \
            and len(self.TASK_TYPES_DICT) == len(self.TASK_TYPES), \
            "The number of task types and probabilities should be the same"
        self.arrival_rate = arrival_rate
        self._validate_task_types()

    def _validate_task_types(self) -> None:
        total_prob = sum(self.TASK_TYPE_PROBS)
        if abs(total_prob - 1) > 1e-10:
            raise ValueError(
                f'Sum of probabilities of task types should be 1, but got {total_prob}')

    def _run_inner(self) -> Generator[Event, None, None]:
        while self.now < self.active_time:
            # HACK: randomly generate the task
            task = self.TASK_TYPES[self.rng
                                   .choice(len(self.TASK_TYPES),
                                           p=self.TASK_TYPE_PROBS)] \
                .from_random(self.world)
            self._submit_task(task)
            # beta = 1/lambda = 1/self.arrival_rate
            beta = 1/self.arrival_rate
            yield self.env.timeout(self.rng.exponential(beta)) \
                | self.env.timeout(self.active_time - self.now + 0.1)


class SubmitterOffline(SubmitterBase['WorldHybridBase', 'TaskHybridBase']):
    def __init__(self, world: 'WorldHybridOffline',  tasks: Sequence['TaskHybridBase']):
        super().__init__(world)
        self.tasks = tasks

    def _run_inner(self) -> Generator[Event, None, None]:
        for task in self.tasks:
            self._submit_task(task)
        yield self.env.timeout(0)
