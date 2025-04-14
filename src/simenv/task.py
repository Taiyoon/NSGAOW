from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Dict, List, Self, Tuple

import numpy as np
import simpy
from loguru import logger

from simenv.base import CpuIntensity, PrivData, TaskId, WorldBase, WorldElemBase
from simenv.utils import deref
from simenv.utils.enums import HybridVMLocation
# from solver.objective import Task

if TYPE_CHECKING:
    from simenv.world import WorldHybridOffline
    from simenv.vm import VmPrivate
    from simenv.vm import VMBase, VMHybridBase
    from simenv.world import WorldHybridBase


class TaskBase[U: 'WorldBase'](
        WorldElemBase[U], ABC):

    class State(Enum):
        UNINIT = auto()           # submitted, but not dispatched to VM
        DISPATCHED = auto()     # dispatched to VM, but did not have VM resource yet
        RUNNING = auto()        # running on VM
        FINISHED = auto()       # finished

    def __init__(self, world: U) -> None:
        super().__init__(world)
        self._state = self.State.UNINIT
        # self.eval_context['state'] = lambda self: self.state
        self.ctxlog.trace('task generated')

    @property
    def state(self) -> State:
        return self._state

    def __del__(self) -> None:
        # FIXME
        return
        if self.state != self.State.FINISHED:
            # self.ctxlog.error(f"Task not finished but deleted")
            raise RuntimeError(f"Task {self} is not finished, but deleted")
        # self.ctxlog.success(f"finished and deleted")

    @property
    def is_uninit(self) -> bool:
        return self.state == self.State.UNINIT

    def dispatch(self) -> None:
        if not self.is_uninit:
            raise RuntimeError(f"Task {self} is not in UNINIT state")
        self._state = self.State.DISPATCHED
        self.ctxlog.info(f"dispatched")

    def run(self) -> None:
        if self.state != self.State.DISPATCHED:
            raise RuntimeError(f"Task {self} is not in DISPATCHED state")
        self._state = self.State.RUNNING
        self.ctxlog.info(f"running")

    def finish(self) -> None:
        if self.state != self.State.RUNNING:
            raise RuntimeError(f"Task {self} is not in RUNNING state")
        self._state = self.State.FINISHED
        self.ctxlog.info(f"finished")

    @abstractmethod
    def request_complete(self) -> None:
        pass


class TaskHybridBase(TaskBase['WorldHybridBase'], ABC):

    def __init__(self, world: 'WorldHybridBase') -> None:
        super().__init__(world)
        self._vm: Tuple | None = None   # type: ignore
        # self.eval_context['vm'] = lambda self: self.vm

    @property
    def vm(self) -> Tuple['VMHybridBase', ...] | None:
        if self._vm is None:
            return None
        return tuple(deref(v) for v in self._vm)

    @vm.setter
    def vm(self, vms: Tuple['VMHybridBase', ...]) -> None:
        self.dispatch()
        if self._vm is None:
            self._vm = tuple(v for v in vms)
        else:
            raise ValueError(f"Task {self} already dispatched")

    @classmethod
    def from_random(cls, world: 'WorldHybridBase') -> Self:
        # HACK: random generate task
        return cls(world, **cls._random_init_data(world))   # type: ignore


class CoopTask(TaskHybridBase):
    @dataclass
    class TaskData:
        data_public: float
        data_private: float
        cycle_public: float
        cycle_private: float
        swap_times: int

    @dataclass
    class Request:
        location: HybridVMLocation
        data: float
        cycle: float

    @property
    def vm(self) -> Tuple['VMHybridBase', ...] | None:
        return super().vm

    @vm.setter
    def vm(self, vms: Tuple['VMHybridBase', ...]) -> None:
        if len(vms) != 2:
            raise ValueError("CoopTask must be dispatched to 2 VMs")
        pub_vm, priv_vm = vms
        if pub_vm.location != HybridVMLocation.PUBLIC or \
                priv_vm.location != HybridVMLocation.PRIVATE:
            raise ValueError(
                f"VM {pub_vm} must be public and {priv_vm} must be private")
        TaskBase.vm.__set__(self, (pub_vm, priv_vm))    # type: ignore

    @property
    def current_request(self) -> Request:
        return self._current_request

    @property
    def left(self) -> TaskData:
        return self.TaskData(
            self.DATA.data_public - self.processed.data_public,
            self.DATA.cycle_public - self.processed.cycle_public,
            self.DATA.data_private - self.processed.data_private,
            self.DATA.cycle_private - self.processed.cycle_private,
            self.DATA.swap_times - self.processed.swap_times
        )

    def request_complete(self) -> None:
        if self.current_request.location == HybridVMLocation.PUBLIC:
            self.processed.data_public += self.current_request.data
            self.processed.cycle_public += self.current_request.cycle
        elif self.current_request.location == HybridVMLocation.PRIVATE:
            self.processed.data_private += self.current_request.data
            self.processed.cycle_private += self.current_request.cycle
        else:
            raise NotImplementedError('unknown location')
        self.processed.swap_times += 1
        if self.swap_times_left == 0:
            self.finish()
        else:
            self._current_request: CoopTask.Request = self._next_request(
                self.current_request)
        self.last_req_finish.succeed()
        self._last_req_finish = self.env.event()
        self.ctxlog.info("request complete")

    def _next_request(self, req: Request) -> Request:
        if req.location == HybridVMLocation.PUBLIC:
            loc = HybridVMLocation.PRIVATE
            data_left = self.DATA.data_private - self.processed.data_private
            cycle_left = self.DATA.cycle_private - self.processed.cycle_private
        elif req.location == HybridVMLocation.PRIVATE:
            loc = HybridVMLocation.PUBLIC
            data_left = self.DATA.data_public - self.processed.data_public
            cycle_left = self.DATA.cycle_public - self.processed.cycle_public
        else:
            raise NotImplementedError('unknown location')
        assert data_left >= 0 and cycle_left >= 0, 'data_left and cycle_left should not be negative'
        left_swap_times = (self.DATA.swap_times -
                           self.processed.swap_times + 1) // 2
        if left_swap_times == 1:
            data = data_left
            cycle = cycle_left
        elif left_swap_times > 1:
            u1, u2 = self.rng.standard_normal(2)
            data = data_left / left_swap_times  # mu
            data += u1 * self.STDDEV * data  # sigma
            data = np.clip(data, 0., data_left)
            cycle = cycle_left / left_swap_times  # mu
            cycle += u2 * self.STDDEV * cycle  # sigma
            cycle = np.clip(cycle, 0., cycle_left)
        else:
            raise ValueError('left_swap_times should not less than 1')
        assert data <= data_left and cycle <= cycle_left, \
            'data and cycle should not be greater than data_left and cycle_left'
        return self.Request(loc, data, cycle)

    @property
    def last_req_finish(self) -> simpy.Event:
        return self._last_req_finish

    @property
    def swap_times_left(self) -> int:
        return self.left.swap_times

    def __init__(self, world: 'WorldHybridBase',
                 data_public: float,   # D^u
                 data_private: float,  # D^p
                 cycle_public: float,  # C^u
                 cycle_private: float,  # C^p
                 swap_times: int      # k
                 ) -> None:
        super().__init__(world)
        self.STDDEV = 0.1
        self.DATA = self.TaskData(
            data_public, data_private, cycle_public, cycle_private, swap_times)
        self.processed = self.TaskData(0., 0., 0., 0., 0)
        self._current_request = self._next_request(
            self.Request(HybridVMLocation.PUBLIC, 0., 0.))
        self._last_req_finish = self.env.event()
        self.const_context['DATA'] = asdict(self.DATA)
        # self.eval_context['processed'] = lambda self: asdict(self.processed)
        # self.eval_context['left'] = lambda self: asdict(self.left)
        self.ctxlog.info(f'initialized')

    @classmethod
    def _random_init_data(cls, world: 'WorldBase') -> Dict[str, float]:
        """
        HACK: Randomly generate task data.

        Returns:
            A dictionary containing the task data.
        """
        rng = world._rng

        def normal(mu: float, sigma: float) -> float:
            res = -1.
            while res < 0:
                res = rng.normal(mu, sigma)
            return res
        # D^u: amount of data to be processed in public cloud
        data_public = normal(15., 2.89)  # Mbit
        # D^p: amount of data to be processed in private cloud
        data_private = normal(15., 2.89)  # Mbit
        # C^u: amount of computation to be done in public cloud
        cycle_public = normal(15., 2.89)  # MC
        # C^p: amount of computation to be done in private cloud
        cycle_private = normal(15., 2.89)  # MC
        # k: number of times to swap between public and private clouds
        swap_times = rng.integers(5, 10)        # times
        return {
            'data_public': data_public,
            'data_private': data_private,
            'cycle_public': cycle_public,
            'cycle_private': cycle_private,
            'swap_times': swap_times,
        }


class PrivTask(TaskHybridBase):
    def __init__(self,
                 world: 'WorldHybridOffline',
                 id: TaskId,
                 compute_intensity: CpuIntensity,
                 data_assignment: PrivData) -> None:
        super().__init__(world)
        self.id = id
        self.compute_intensity = compute_intensity
        self.data_assignment = data_assignment
        
        # Task Protocol
        self.ID = id
        self.DATA = self.data_assignment
        self.O_PROC = self.compute_intensity

    def request_complete(self) -> None:
        self.ctxlog.info("request complete")
        
    def __repr__(self):
        return f'PrivTask id: {self.id}'
