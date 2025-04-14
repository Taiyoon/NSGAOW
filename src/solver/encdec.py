from functools import cache
from typing import Dict, Iterable, List, Sequence, Tuple

from simenv.base import PrivData
from simenv.task import PrivTask
from simenv.vm import VmPrivate, VmPublic
from simenv.world import WorldHybridOffline
from solver.objective import DataResult, ObjectiveCalc, TaskResult

import numpy as np


class WorldEnDecoder:
    def __init__(self, world: WorldHybridOffline, rng=np.random.default_rng(42)) -> None:
        '''
        
        '''
        self.priv_vm: List[VmPrivate] = world.priv_vm_list
        self.pub_vm: List[VmPublic] = world.pub_vm_list
        self.task: List[PrivTask] = world.tasks
        self.data: List[PrivData] = world.priv_data_list
        self.bandwidth = world.bandwidth
        self.propagation_delay = world.propagation_delay
        self.o_transback = 0.1
        self._ind_info = {
            'X': {},
            'Y': {},
            'Z_enc': {},
            'Z_offload': {}
        }
        max_security = sum(d.SIZE for d in self.data)
        self._obj_info = {
            'security': {'max': max_security}
        }
        self.obj_func = ObjectiveCalc(
            self.priv_vm,
            self.pub_vm,
            self.data,
            self.bandwidth,
            self.propagation_delay,
            self.o_transback,
            world.compact_data_indices(),
            self.task)
        self.rng = rng

    def convert_security_objective(self, security: np.ndarray) -> np.ndarray | float:
        max_sec = self._obj_info['security']['max']
        return np.float64(max_sec) - security
    
    @cache
    def encode_sequence(self) -> List[Tuple[int, int]]:

        X = [
            (0, len(t.data_assignment.storage_nodes)) for t in self.task
        ]
        self._ind_info['X']['len'] = len(X)
        Y = [(0, len(self.pub_vm))] * len(self.task)
        self._ind_info['Y']['len'] = len(X)
        Z_enc = [
            (0, len(d.valid_schemes)) for d in self.data if len(d.valid_schemes) > 0
        ]
        self._ind_info['Z_enc']['len'] = len(Z_enc)
        Z_offload = [(0, 2)] * len(self.task)
        self._ind_info['Z_offload']['len'] = len(X)
        # print('enc', len(X), len(Y), len(Z_enc), len(Z_offload))
        return X + Y + Z_enc + Z_offload

    def encseq(self) -> np.ndarray:
        ans = np.array(self.encode_sequence())
        # print(ans.shape)
        return ans

    def sep_pop(self, indivual: List[int]) -> Dict['str', List[int]]:
        ans = {}
        a = len(indivual)
        b = sum(v['len'] for v in self._ind_info.values())
        c = len(self.task)*3 + len(self.data)
        d = len(self.encode_sequence())
        # print('code length: ', a, b, c, d)
        for k, v in self._ind_info.items():
            ans[k] = indivual[:v['len']]
            indivual = indivual[v['len']:]
        # print(indivual)
        assert len(indivual) == 0
        return ans

    def decode_sequence(self, indivual: List[int]) -> Tuple[List[TaskResult], List[DataResult]]:
        valid_data = sum(1 for data in self.data if len(data.valid_schemes) > 0)
        # print(f'valid_data: {valid_data}')
        # print(f'task {len(self.task)}')
        ans = [TaskResult() for _ in self.task], [DataResult() for _ in range(valid_data)]
        # HACK
        old_ind = indivual
        indivual = []
        for n, (a, b) in zip(old_ind, self.encode_sequence()):
            if n < a or n >= b:
                # print(f'out of range {n}, ({a, b})')
                # indivual = [0] * len(indivual)
                n = b-1
            indivual.append(n)
        # indivual = np.clip(indivual, 0, np.array(self.encode_sequence())[:, 1]-1)
        X, Y, Z_enc, Z_offload = self.sep_pop(indivual).values()
        for m, code in enumerate(X):
            t: PrivTask = self.task[m]
            ans[0][m].task = t
            ans[0][m].priv_vm = t.data_assignment.storage_nodes[code]
        for m, code in enumerate(Y):
            ans[0][m].pub_vm = self.pub_vm[code]
        data_ind = 0
        for k in range(len(self.data)):
            if self.data[k].valid_schemes == []:
                continue
            code = Z_enc[data_ind]
            d: PrivData = self.data[k]
            ans[1][data_ind].data = d
            ans[1][data_ind].scheme = d.valid_schemes[code]
            data_ind += 1
        for m, code in enumerate(Z_offload):
            if ans[0][m].task.DATA.valid_schemes == []:
                ans[0][m].is_coop = 0
            else:
                ans[0][m].is_coop = code
        # for _ in g:
        #     raise ValueError('too many codes')
        assert len(set(self.task)) == len(self.task)
        tasks = set(tr.task for tr in ans[0])
        assert len(tasks) == len(ans[0])
        return ans

    def makespan(self, indivual: Iterable[int]) -> Tuple[float]:
        ans, = self.obj_func.multi_objective(
            *self.decode_sequence(indivual), ['makespan'])
        return ans,

    def three_obj(self, indivual: Iterable[int]) -> Tuple[float, float, float]:
        ans = self.obj_func.multi_objective(
            *self.decode_sequence(indivual), ['makespan', 'security', 'cost'])
        return tuple(ans)
    def two_obj(self, indivual: Iterable[int]) -> Tuple[float, float, float]:
        ans = self.obj_func.multi_objective(
            *self.decode_sequence(indivual), ['makespan', 'security'])
        return tuple(ans)

    def print_time(self, indivual: Iterable[int]):
        ans = self.obj_func.multi_objective(
            *self.decode_sequence(indivual), [], True)

    def rand_init(self):
        li = self.encseq()
        ans = self.rng.integers(li[:, 0], li[:, 1])
        assert len(ans) == len(li)
        for r in ans:
            yield r


class RawNSGA2Encoder(WorldEnDecoder):
    def decode_sequence(self, indivual: List[float]):
        # offload_num = self._ind_info['Z_offload']['len']
        scaled = np.array(indivual) * self.encseq()[:, 1]
        # scaled[-offload_num:] = scaled[-offload_num:][lambda x:x>0.5]
        scaled = np.round(scaled).astype(int)
        return super().decode_sequence(scaled)
