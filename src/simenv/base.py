from simenv.privacy import PrivacySchemeList
from typing import NewType
from dataclasses import dataclass, field
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property, partial
from io import StringIO
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Container, Dict, List, Literal, NewType, NoReturn, Self

from loguru import logger
import numpy as np
import simpy

from simenv.utils.traits import Loggable

from simenv.utils import deref

if TYPE_CHECKING:
    from simenv.vm import VmPrivate
    from simenv.submitter import SubmitterBase
    from simenv.world_scheduler import WorldSchedulerBase


class Base(ABC):
    _alloc_id = 0

    def __init__(self) -> None:
        self.id = Base._alloc_id
        Base._alloc_id += 1
        self.const_context: Dict[str, Any] = {
            'id': self.id, 'type': type(self).__name__}
        self.eval_context: Dict[str, Callable[[Any], Any]] = {}

    def __str__(self) -> str:
        return f'{self.__class__.__name__}_id_{self.id}'


class WorldBase(Base, Loggable, ABC):
    def __init__(self, seed: int) -> None:
        super().__init__()
        self._env = simpy.Environment()
        self.SEED = seed
        self._rng = np.random.default_rng(self.SEED)
        self._rng1, = self._rng.spawn(1)

    def __str__(self) -> str:
        return f'{super().__str__()}_seed{self.SEED}'

    @property
    def env(self) -> simpy.Environment:
        return self._env

    @property
    @abstractmethod
    def task_submitter(self) -> 'SubmitterBase':  # type: ignore[type-arg]
        pass

    @property
    @abstractmethod
    def scheduler(self) -> 'WorldSchedulerBase':
        pass


class WorldElemBase[T: 'WorldBase'](Base, Loggable, ABC):

    def __init__(self, world: T) -> None:
        super().__init__()
        self._world = world
        # FIXME
        # def time(env: simpy.Environment) -> float:
        #     return env.now
        # self.eval_context['simtime'] = partial(time, env=self.env)

    @property
    def world(self) -> T:
        return self._world

    @property
    def env(self) -> simpy.Environment:
        return self.world._env

    @property
    def now(self) -> int | float:
        return self.env.now

    @property
    def rng(self) -> np.random.Generator:
        """
        A RNG for task sequence generation.

        Returns:
            A numpy random number generator instance.
        """
        return self.world._rng


class SchedulerBase[T: 'WorldBase'](WorldElemBase[T], ABC):
    def __init__(self, world: T) -> None:
        super().__init__(world)

# type defs

# VM


PrivVmId = NewType('PrivVmId', int)
PubVmId = NewType('PubVmId', int)
CpuSpeed = NewType('CpuSpeed', float)
Cost = NewType('Cost', float)
PubVmType = NewType('PubVmType', int)

# World

BandWidth = NewType('BandWidth', float)
PropagationDelay = NewType('PropagationDelay', float)

# Data

PrivSchemeType = NewType('PrivSchemeType', int)
DataId = NewType('DataId', int)
# 有些数据只允许在私有云中运算，因此我们去除这部分编码，提高编码效率
CompactDataId = NewType('CompactDataId', int)
DataSize = NewType('DataSize', float)
DataSecurity = NewType('DataSecurity', float)
CpuIntensity = NewType('CpuIntensity', float)


@dataclass
class PrivacyScheme:
    SECURITY: DataSecurity
    O_ENC: CpuIntensity
    O_DEC: CpuIntensity


class PrivacySchemeTable:
    def __init__(self, type_id: PrivSchemeType, schemes: List[PrivacyScheme]):
        self.type_id = type_id
        # inf = float('inf')
        # schemes.append(PrivacyScheme(inf, inf, inf))  # type: ignore
        def skey(x: PrivacyScheme) -> float:
            return x.SECURITY
        self.schemes = sorted(schemes, key=skey, reverse=True)


@dataclass
class PrivData:
    AbsId: DataId
    ID: DataId
    preference_type: PrivacySchemeTable
    SIZE: DataSize
    min_security: DataSecurity
    storage_nodes: List['VmPrivate']
    security_history: DataSecurity = field(default=1.0)

    @cached_property
    def valid_schemes(self) -> List[PrivacyScheme]:
        return [ps for ps in self.preference_type if ps.SECURITY > self.min_security]

# Task


TaskId = NewType('TaskId', int)
