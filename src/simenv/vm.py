from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING, Any, Generator

import simpy

from simenv.base import Cost, CpuSpeed, PrivVmId, PubVmId, PubVmType, WorldBase, WorldElemBase
from simenv.task import CoopTask
from simenv.utils.enums import HybridVMLocation
from simenv.utils.traits import DepRunnable
from simenv.vm_scheduler import VMSchedulerBase, VMSchedulerFIFO
# from solver.makespan import VM

if TYPE_CHECKING:
    from simenv.task import TaskHybridBase
    from simenv.world import WorldHybridBase


class VMBase[T: WorldBase](WorldElemBase[T], ABC):

    def __init__(self, world: T) -> None:
        super().__init__(world)


class VMHybridBase(VMBase['WorldHybridBase']):
    def __init__(self, world: 'WorldHybridBase') -> None:
        super().__init__(world)
        self._scheduler = VMSchedulerFIFO(self)

    @property
    def location(self) -> HybridVMLocation:
        return self.world.vm_location(self)

    @property
    def scheduler(self) -> VMSchedulerBase:
        return self._scheduler

    @abstractmethod
    # type: ignore
    def process(self, *args, **kwargs) -> Generator[simpy.Event, None, None]:
        pass


class VMHybrid(VMHybridBase):
    def __init__(self, world: 'WorldHybridBase', id: int) -> None:
        super().__init__(world)
        self._scheduler = VMSchedulerFIFO(self)
        self._cpu = simpy.Resource(self.env, capacity=1)
        self._net = simpy.Resource(self.env, capacity=1)
        self.CPU_SPEED = 100.
        self.NET_SPEED = 100.
        self.const_context['cpu_speed'] = self.CPU_SPEED
        self.const_context['net_speed'] = self.NET_SPEED

    @property
    def location(self) -> HybridVMLocation:
        return self.world.vm_location(self)

    def process(self,  # type: ignore
                data: float,
                cycle: float) -> Generator[simpy.Event, None, None]:
        with self._net.request() as req:
            yield self.env.timeout(data / self.NET_SPEED)
        with self._cpu.request() as req:
            yield self.env.timeout(cycle / self.CPU_SPEED)


class VmPrivate(VMHybridBase):
    def __init__(self, world: 'WorldHybridBase', id: PrivVmId, compute_capacity: float) -> None:
        super().__init__(world)
        self.id: PrivVmId = id
        self.compute_capacity = compute_capacity

        # VM Protocol (Legacy, but in use)
        self.ID = id
        self.TYPE = 'Private'
        self.CPU = compute_capacity

    def process(self, *args, **kwargs):
        pass

    def __repr__(self):
        return f'VmPrivate id: {self.id}'


class VmPublic(VMHybridBase):
    def __init__(self, world: 'WorldHybridBase', id: PubVmId, type_id: PubVmType, compute_capacity: CpuSpeed, cost: Cost) -> None:
        super().__init__(world)
        self.id = id
        self.type_id = type_id
        self.compute_capacity = compute_capacity
        self.cost = cost

        # VM Protocol
        self.ID = id
        self.TYPE = 'Public'
        self.CPU = compute_capacity
        self.COST = cost

    def process(self, *args, **kwargs):
        pass

    def __repr__(self):
        return f'VmPublic id: {self.id}'
