from functools import cached_property
import os
from pprint import pprint
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from io import StringIO
from typing import (TYPE_CHECKING, Any, Container, Dict, Generator, List, Literal, Mapping,
                    Sequence, TextIO, Type)

import numpy as np
import simpy
from loguru import logger
from numpy.typing import ArrayLike, NDArray

from simenv.base import BandWidth, Base, CompactDataId, DataId, PrivData, PrivSchemeType, PrivacyScheme, PrivacySchemeTable, PropagationDelay, WorldBase
from simenv.config_parser import Config, ConfigParser
from simenv.submitter import SubmitterBase, SubmitterHybridDefault, SubmitterOffline
from simenv.task import CoopTask, PrivTask, TaskHybridBase
from simenv.utils import HybridVMLocation
from simenv.utils.traits import DepRunnable, Loggable
from simenv.vm import VMBase, VMHybrid, VMHybridBase, VmPrivate, VmPublic
from simenv.world_scheduler import SchedulerOffline, WorldSchedulerBase


class WorldHybridBase(WorldBase, DepRunnable, ABC):

    def __init__(self, logto: Container[Literal['stdout', 'file', 'stringio', 'pipe']]) -> None:
        # type define
        self.VMNUM: int
        self.PRIV_VMNUM: int
        self._scheduler: WorldSchedulerBase
        # 介似麻？
        self.DELTA_TIME = 0.01
        self._task_submitter: SubmitterBase['WorldHybridBase', TaskHybridBase]

        super().__init__(42)
        self._vms: List[VMHybridBase] = []
        logger.remove()
        if 'stdout' in logto:
            logger.add(sys.stdout, level='TRACE')
        if 'file' in logto:
            logger.add(f'./log/{str(self)}_{datetime.now().strftime("%Y%m%d%H%M%S")
                                            }.json',  level='TRACE', serialize=True, backtrace=True, diagnose=True)
        if 'stringio' in logto:
            self.stringio = StringIO()
            logger.add(self.stringio,  level='TRACE', serialize=True,
                       backtrace=True, diagnose=True)
        if 'pipe' in logto:
            rx_fd, tx_fd = os.pipe()
            self._rx = os.fdopen(rx_fd, 'r', encoding='utf-8')
            self._tx = os.fdopen(tx_fd, 'w', encoding='utf-8')
            logger.add(self._tx,  level='TRACE', serialize=True,
                       backtrace=True, diagnose=True)
        self.const_context['seed'] = self.SEED
        self.ctxlog.info('Initializing world...')

    def _add_vm(self, vm: VMHybridBase) -> None:
        self._vms.append(vm)

    def vm_location(self, vm: VMHybridBase) -> Literal[HybridVMLocation.PRIVATE] | Literal[HybridVMLocation.PUBLIC]:
        assert vm.world is self and self._vms[vm.id] is vm, f"VM {
            vm} not in world {self}"
        if vm.id < self.PRIV_VMNUM:
            return HybridVMLocation.PRIVATE
        else:
            return HybridVMLocation.PUBLIC

    @property
    def scheduler(self) -> 'WorldSchedulerBase':
        return self._scheduler

    @property
    def pipe(self) -> TextIO:
        raise NotImplementedError('Pipe not implemented yet')
        return self._rx

    def _run_inner(self) -> Generator[simpy.Event, None, None]:  # type: ignore
        print(f'Starting hybrid world at {self.env.now}')
        self.add_dependent(self.task_submitter)
        self.add_dependent(self.scheduler)
        self.task_submitter.run()
        self.scheduler.run()
        for vm in self._vms:
            vm_scheduler = vm.scheduler
            self.add_dependent(vm_scheduler)
            vm_scheduler.run()
        yield simpy.AllOf(self.env, self.dependent_runnables)
        if hasattr(self, '_tx'):
            self._tx.close()

    @property
    def task_submitter(self) -> SubmitterBase['WorldHybridBase', TaskHybridBase]:
        return self._task_submitter

    def __str__(self) -> str:
        members = {
            'len(priv_vm)': self.PRIV_VMNUM,
        }
        return f'{super().__str__()}: {members}'


class WorldHybrid(WorldHybridBase):
    def __init__(self, logto: Container[Literal['stdout', 'file', 'stringio', 'pipe']], arrival_rate: float = 10.) -> None:
        self.VMNUM = 40
        self.PRIV_VMNUM = 10
        self.active_time = 10.
        self._task: List['TaskHybridBase'] = []
        self.ARRIVAL_RATE = arrival_rate
        super().__init__(logto)
        self._task_submitter = SubmitterHybridDefault(
            self,
            self.active_time,
            self.ARRIVAL_RATE,
            {
                CoopTask: 1.
            })
        # self._scheduler = WorldSchedulerDefault(self, self.DELTA_TIME)
        for i in range(self.VMNUM):
            self._add_vm(VMHybrid(self, i))
        self.init_deprun()

    def start(self, until: float | None = None) -> None:
        self.run()
        self.env.run()


class WorldHybridOffline(WorldHybridBase):
    def __init__(self,
                 logto: Container[Literal['stdout', 'file', 'stringio', 'pipe']],
                 config: Config | str) -> None:
        if isinstance(config, str):
            # HACK
            config = ConfigParser(config, np.random.default_rng(42)).config
        # read config
        assert isinstance(config, dict)
        cloud = config['cloud']

        assert isinstance(cloud, dict)
        private_vms = cloud['private_vms']
        assert isinstance(private_vms, list)
        self.PRIV_VMNUM = len(private_vms)

        public_vms = cloud['public_vms']
        assert isinstance(public_vms, list)
        self.VMNUM = len(private_vms) + len(public_vms)

        network = cloud['network']
        self.bandwidth: BandWidth = network['bandwidth']    # type: ignore
        self.propagation_delay: PropagationDelay =\
            network['propagation_delay']  # type: ignore

        self.priv_scheme_tables: Dict[PrivSchemeType, PrivacySchemeTable] = {}
        priv_table = config['privacy_schemes']['preferences']  # type: ignore
        assert isinstance(priv_table, list)
        for pt_conf in priv_table:
            self.priv_scheme_tables[
                pt_conf['type_id']] = [  # type: ignore
                PrivacyScheme(*st)  # type: ignore
                for st in pt_conf['strategies']]  # type: ignore

        # init world
        super().__init__(logto)
        self._scheduler = SchedulerOffline(self)
        for id, vm_conf in enumerate(private_vms):
            assert isinstance(vm_conf, dict)
            compute_capacity = vm_conf['compute_capacity']
            assert isinstance(compute_capacity, float)
            self._add_vm(
                VmPrivate(self, id, compute_capacity)  # type: ignore
            )
        for id, vm_conf in enumerate(public_vms):
            assert isinstance(vm_conf, dict)
            compute_capacity = vm_conf['compute_capacity']
            assert isinstance(compute_capacity, float | int)
            type_id = vm_conf['type_id']
            assert isinstance(type_id, int)
            cost = vm_conf['cost']
            assert isinstance(cost, float)
            self._add_vm(
                VmPublic(self, id, type_id, compute_capacity,  # type: ignore
                         cost)  # type: ignore
            )

        pd_conf = config['privacy_data']
        priv_data_list: List[PrivData] = []
        for id, d in enumerate(pd_conf):  # type: ignore
            args = [id,id,
                    self.priv_scheme_tables[
                        d['preference_type']],  # type: ignore
                    d['size'],  # type: ignore
                    d['min_security'],  # type: ignore
                    [self.priv_vm_list[n_idx]  # type: ignore
                     for n_idx in d['storage_nodes_indices']]]  # type: ignore
            # pprint(args)
            priv_data_list.append(
                PrivData(*args)  # type: ignore
            )
        self.PRIV_DATA_NUM: int = len(priv_data_list)

        self.tasks: List[PrivTask] = []
        t_conf = config['tasks']
        for id, t in enumerate(t_conf):  # type: ignore
            self.tasks.append(
                PrivTask(self, id,  # type: ignore
                         t['compute_intensity'],  # type: ignore
                         priv_data_list[
                             t['data_assignment']])  # type: ignore
            )

        # 过滤不需要的data
        data_tasks: Dict['DataId', 'PrivTask'] = {}
        for t in self.tasks:
            data = t.DATA
            tl = data_tasks.setdefault(data.ID, [])
            tl.append(t)

        self.priv_data_list = []
        data_id = 0
        for k, v in data_tasks.items():
            data = priv_data_list[k]
            data.ID = data_id
            data_id += 1
            self.priv_data_list.append(data)

        # attatch other runnable compoments
        self._task_submitter = SubmitterOffline(self, self.tasks)
        self.init_deprun()

    def start(self, until: float | None = None) -> None:
        self.run()
        self.env.run()

    @property
    def priv_vm_list(self) -> List[VmPrivate]:
        res = self._vms[:self.PRIV_VMNUM]
        assert all(isinstance(vm, VmPrivate) for vm in res)
        return res  # type: ignore

    @property
    def pub_vm_list(self) -> List[VmPublic]:
        res = self._vms[self.PRIV_VMNUM:]
        assert all(isinstance(vm, VmPublic) for vm in res)
        return res  # type: ignore

    def compact_data_indices(self) -> Mapping[DataId, CompactDataId]:
        compact_id: CompactDataId = 0
        ans = {}
        for i, d in enumerate(self.priv_data_list):
            if d.valid_schemes == []:
                continue
            ans[i] = compact_id
            compact_id += 1
        return ans


if __name__ == '__main__':
    conf = ConfigParser('src/config1.yml').config
    w = WorldHybridOffline(('stdout',), conf)
    w.start()
    print(w)
