import pprint
from dataclasses import dataclass, field
from collections import Counter, deque
from typing import Deque, List, Literal, Mapping, Protocol, Optional, Set, Tuple, TYPE_CHECKING, cast
from typing import Any, Callable, Literal, Protocol, Sequence

import numba
import numpy as np

from simenv.base import CompactDataId, DataId


if TYPE_CHECKING:
    from simenv.task import PrivTask
    from simenv.base import PrivacyScheme
    from simenv.base import PrivData
    from simenv.vm import VmPrivate, VmPublic


DATAID = int
TASKID = int
VMID = int


# class Data(Protocol):
#     """数据实体协议，包含隐私方案偏好和大小"""
#     ID: DATAID
#     PREF: 'PrivacySchemeList'
#     SIZE: float
#     min_security: float
#     security_history: float


# class Task(Protocol):
#     """计算任务定义"""
#     ID: TASKID
#     DATA: 'PrivData'
#     O_PROC: float  # 处理开销系数


# class PrivacyScheme(Protocol):
#     """隐私方案协议，定义安全参数"""
#     SECURITY: float  # 安全等级
#     O_ENC: float     # 加密开销系数
#     O_DEC: float     # 解密开销系数


# PrivacySchemeList = Sequence[PrivacyScheme]

# TODO: 人类可读的任务调度结果


@dataclass
class TaskResult:
    """任务调度结果"""
    task: 'PrivTask' = field(init=False)
    pub_vm: 'VmPublic' = field(init=False)     # 分配的公有云虚拟机（延迟初始化）
    priv_vm: 'VmPrivate' = field(init=False)    # 分配的私有云虚拟机（延迟初始化）
    is_coop: bool = field(init=False)    # 是否为协作任务（延迟初始化）


def dummy_task_result(task: 'PrivTask') -> TaskResult:
    return TaskResult(None, None, None, None)


@dataclass
class DataResult:
    """数据隐私方案选择结果"""
    data: 'PrivData' = field(init=False)           # 延迟初始化
    scheme: 'PrivacyScheme' = field(init=False)  # 延迟初始化

    def __repr__(self):
        return f'DataRes: {self.data} {self.scheme}'


def dummy_data_result(data: 'PrivData') -> DataResult:
    return DataResult(None, None)


class Workload:
    """带依赖关系的工作负载"""

    def __repr__(self):
        if self.task == None:
            return 'dummy'
        return f'{self.task.ID} {self.name}'

    @classmethod
    def dummy(cls) -> 'Workload':
        return Workload(0, None, 'dummy')

    def __init__(self, time: float, task: 'PrivTask', name: str, dep: Optional[Set['Workload']] = None):
        """
        :param time: 任务持续时间
        :param task: 关联的任务对象
        :param dep: 依赖的工作负载集合
        """
        self.dependency: Set[Workload] = dep if dep is not None else set()
        self.TIME = time
        self.task = task
        self._start_time = 0.0
        self.next: Optional[Workload] = None
        self.name = name
        self._last_dep = dep if dep is not None else set()

    @property
    def start_time(self) -> float:
        """动态计算开始时间"""
        # print(f'me: {self} deps: {self.dependency}')
        if self._last_dep != self.dependency:
            self._last_dep = self.dependency
            self._start_time = max(
                [w.finish_time for w in self.dependency], default=0.0)
        return self._start_time

    @property
    def finish_time(self) -> float:
        """完成时间计算"""
        return self.start_time + self.TIME

    def add_dependency(self, other: 'Workload') -> None:
        # print(f'me: {self} -> other {other}, dep: {self.dependency}')
        # repr(self)
        """安全添加依赖关系，防止循环依赖"""
        # 已排除依赖错误，为了减少目标计算量，不再检测循环
        self.dependency.add(other)
        # if not self._is_ancestor(other):
        # else:
        # print(f"检测到依赖: {self} -> {other}")
        # ...

    def _is_ancestor(self, node: 'Workload') -> bool:
        # return False
        """广度优先搜索检测闭环"""
        visited: Set[Workload] = set()
        queue: list[Workload] = [self]

        while queue:
            current = queue.pop(0)
            if current == node:
                return True
            if current not in visited:
                visited.add(current)
                queue.extend(current.dependency)
        return False


# HACK: Annotation
# class PrivTask(PrivTask):
#     def __init__(self, world, id, compute_intensity, data_assignment):
#         super().__init__(world, id, compute_intensity, data_assignment)
#         self.works: List[Workload]


# 创新，保证O(n)复杂度
OwLeftTry = 5


class OpputunityWindow:
    def __init__(self, front: List[Workload], rear: List[Workload]) -> None:
        self.front = front
        self.rear = rear
        self.left_try = OwLeftTry


class OpputunityVM:
    def __init__(self, vm: 'VmPrivate') -> None:
        self.inner = vm
        self.ow: Deque[OpputunityWindow] = deque()
        self.last_cpu: Workload = Workload.dummy()
        self.last_net: Workload = Workload.dummy()
        self.wait_to_schedule: List['PrivTask'] = []


class ObjectiveCalc:
    ALPHA = 4.

    def __init__(self,
                 priv_pool: Sequence['VmPrivate'],
                 pub_pool: Sequence['VmPublic'],
                 data_pool: Sequence['PrivData'],
                 bandwidth: float,            # 网络带宽 (Mbps)
                 propagation_delay: float,    # 网络传输延迟 (s)
                 o_transback: float,          # 返程传输开销系数):
                 compact_data_id: Mapping[DataId, CompactDataId],
                 tasks: Sequence['PrivTask']
                 ) -> None:
        self.priv_pool = priv_pool
        self.pub_pool = pub_pool
        self.data_pool = data_pool
        self.bandwidth = bandwidth
        self.propagation_delay = propagation_delay
        self.o_transback = o_transback
        self.cid = compact_data_id
        self.tasks = tasks
        self.norm_security = 0.
        for task in self.tasks:
            self.norm_security += task.DATA.SIZE

        self.avg_pub_cpu = sum(v.CPU for v in pub_pool) / len(pub_pool)
        self.avg_priv_apu = sum(v.CPU for v in priv_pool) / len(priv_pool)

    def multi_objective(self, task_results: Sequence[TaskResult], data_schemes: Sequence[DataResult], objectives: Sequence[Literal['makespan', 'security', 'cost', 'sat_ddl_cnt', 'priv_utils']], stat_time: bool = False) -> List[float]:
        assert len(objectives) <= 3 and len(set(objectives)) == len(objectives)
        res = []
        works = self._works(task_results, data_schemes)
        # tasks = [r.task for r in task_results]
        for objective in objectives:
            if objective == 'makespan':
                makespan = max(max(ft.finish_time for ft in work)
                               for work in works)
                assert makespan > 0.
                res.append(makespan)
            elif objective == 'security':
                sec = 0.    
                # old objective
                # no_pub = [True] * len(self.data_pool)
                # debug_hist_schemes = []
                # for t_res in task_results:
                #     if t_res.is_coop:
                #         no_pub[t_res.task.DATA.ID] = False
                # for d_res in data_schemes:
                #     if no_pub[self.cid[d_res.data.ID]]:
                #         a_hist = 1.
                #     else:
                #         a_hist = d_res.scheme.SECURITY
                #     debug_hist_schemes.append(a_hist)
                #     a_min = d_res.data.min_security
                #     size = d_res.data.SIZE
                #     # HACK
                #     sec += size * (1-a_hist)
                # new objective
                data_security = {}
                for dr in data_schemes:
                    data_security[dr.data.AbsId] = dr.scheme.SECURITY
                for tr in task_results:
                    if tr.is_coop:
                        # if tr.task.DATA.AbsId not in data_security:
                        #     print(tr.task.DATA)
                        #     continue
                        sec += tr.task.DATA.SIZE * (1-data_security[tr.task.DATA.AbsId])
                assert sec >= 0.
                sec /= self.norm_security
                res.append(sec)
            elif objective == 'cost':
                pub_vm_online = [0.] * len(self.pub_pool)
                for tid, work in enumerate(works):
                    if len(work) == 7:  # is coop
                        ft = work[4].finish_time
                        vmid = task_results[tid].pub_vm.ID
                        pub_vm_online[vmid] = max(pub_vm_online[vmid], ft)
                cost = sum(vm.COST * ft for vm,
                           ft in zip(self.pub_pool, pub_vm_online))
                assert cost >= 0.
                cost /= 3600.  # 一个小时有那么多个秒，想要改整个程序的时间单位？没门
                res.append(cost)
            elif objective == 'sat_ddl_cnt':
                res.append(self.statisfy_deadline_count(works))
            elif objective == 'priv_utils':
                res.append(self.priv_utils(task_results))
            else:
                raise ValueError(f"Unknown objective: {objective}")

        def _stat_time() -> None:
            it, cp = [], []
            for work in works:
                if len(work) == 7:  # is coop
                    cp.append(work[-1].finish_time - work[0].start_time)
                elif len(work) == 1:
                    it.append(work[0].finish_time - work[0].start_time)
            pprint.pprint({
                'avg_it': sum(it) / max(len(it), 1),
                'avg_cp': sum(cp) / max(len(cp), 1),
            })
        if stat_time:
            _stat_time()
        return res

    def est_proc_time(self, tasks: 'PrivTask') -> float:
        pub_cpu = self.avg_pub_cpu
        priv_cpu = self.avg_priv_apu
        priv_time = tasks.DATA.SIZE * tasks.compute_intensity / priv_cpu
        if len(tasks.data_assignment.valid_schemes) == 0:
            return priv_time
        scheme = tasks.data_assignment.valid_schemes[-1]
        enc = scheme.O_ENC + 0.1*scheme.O_DEC
        pub_time = tasks.DATA.SIZE * \
            (tasks.compute_intensity + enc) / pub_cpu + \
            tasks.DATA.SIZE*1.1 / self.bandwidth
        return (priv_time+pub_time) / 2

    def statisfy_deadline_count(self, works: List[Tuple[Workload, ...]], alpha: float | None = None) -> int:
        '返回满足截止时间的任务计数'
        res = 0
        if alpha == None:
            alpha = self.ALPHA
        for work in works:
            t = work[-1].task
            if self.est_proc_time(t) * alpha > work[-1].finish_time - work[0].start_time:
                res += 1
        return res

    def priv_utils(self, task_results: Sequence[TaskResult]) -> float:
        '返回0-1之间的归一化数'
        all_workload = 0.
        priv_workload = 0.
        for r in task_results:
            workload = r.task.DATA.SIZE * r.task.compute_intensity
            all_workload += workload
            if r.is_coop:
                priv_workload += workload
        return priv_workload / all_workload

    def _works(self, task_results: Sequence[TaskResult], data_schemes: Sequence[DataResult]) -> List[Tuple[Workload, ...]]:
        """
        计算系统总makespan
        :param task_results: 任务分配结果
        :param data_schemes: 数据方案选择结果
        :return: 最大完成时间
        """

        priv_pool = self.priv_pool
        pub_pool = self.pub_pool
        bandwidth = self.bandwidth
        propagation_delay = self.propagation_delay
        o_transback = self.o_transback

        # 为所有任务初始化工作负载
        # works: List[Tuple[Workload, ...]] = []
        for t_res in task_results:
            task = t_res.task
            size = task.DATA.SIZE
            priv_cpu = t_res.priv_vm.CPU
            o_proc = task.O_PROC
            if t_res.is_coop:
                pub_cpu = t_res.pub_vm.CPU
                scheme = data_schemes[self.cid[task.DATA.ID]].scheme

                o_enc = scheme.O_ENC
                o_dec = scheme.O_DEC
                task.DATA.security_history = min(
                    task.DATA.security_history, scheme.SECURITY)

                t: Tuple[Workload, ...] = (
                    Workload(size * o_enc / priv_cpu, task, '0'
                             ),  # CPU加密 0
                    Workload(size / bandwidth +
                             # 私有云网络 1
                             propagation_delay, task, '1'),
                    Workload(size / bandwidth +
                             # 公有云网络 2
                             propagation_delay, task, '2'),
                    Workload(size * o_proc / pub_cpu, task, '3'
                             ),  # 公有云CPU处理 3
                    Workload(size * o_transback / bandwidth +
                             # 公有云网络 4
                             propagation_delay, task, '4'),
                    Workload(size * o_transback / bandwidth + propagation_delay                             # 私有云网络
                             , task, '5'),
                    Workload(size * o_dec / priv_cpu * o_transback, task, '6'
                             ),  # CPU验证
                )
                t[1].add_dependency(t[0])
                t[2].add_dependency(t[0])
                t[3].add_dependency(t[1])
                t[3].add_dependency(t[2])
                t[4].add_dependency(t[3])
                t[5].add_dependency(t[3])
                t[6].add_dependency(t[4])
                t[6].add_dependency(t[5])
            else:
                t = Workload(size * o_proc / priv_cpu, task, 'SA'
                             ),  # CPU处理
            task.works = t
        ALL_WORKS = sum(len(tres.task.works) for tres in task_results)
        # 检查所有负载都分配了
        all_works_num = sum(len(tres.task.works) for tres in task_results)

        # 将所有（P）任务按照FCFS放到各自虚拟机队列里
        for vm in pub_pool:
            vm.last_net = Workload.dummy()
        for t_res in task_results:
            if t_res.is_coop:
                all_works_num -= 3
                vm = t_res.pub_vm
                net1 = t_res.task.works[2]
                net2 = t_res.task.works[4]
                p_net = vm.last_net
                net1.add_dependency(p_net)
                vm.last_net = net2
        d = ALL_WORKS - all_works_num - \
            sum(3 for tres in task_results if tres.is_coop)
        assert d == 0, f'有{d}个公有云任务没有分配'

        # 然后，把（E）、（V）、（SA）任务放到私有云队列里
        # 为每个私有虚拟机分配任务
        oppo_pool = [OpputunityVM(vm) for vm in priv_pool]
        for t_res in task_results:
            oppo_pool[t_res.priv_vm.ID].wait_to_schedule.append(t_res.task)

        def is_coop(task: 'PrivTask') -> bool:
            s = len(task.works)
            if s == 7:
                return True
            elif s == 1:
                return False
            else:
                raise RuntimeError(f'task.work: {task.work}')

        # for vm in oppo_pool:
        # 需要严格按照下标顺序排序，以免依赖计算出错
        vm_first_works_num = sum(
            1 for vm in oppo_pool if len(vm.wait_to_schedule) > 0)
        for tres in task_results:
            vm = oppo_pool[tres.priv_vm.ID]
            this_works_num = len(tres.task.works)
            if len(vm.wait_to_schedule) > 0 and repr(vm.last_cpu) == 'dummy' and repr(vm.last_net) == 'dummy':
                # 需要为有任务的虚拟机分配初始负载
                vm_first_works_num -= 1
                this_works_num -= 1
                # 虚拟机最后的任务，若无机会窗口，则任务排在它之后
                vm.last_cpu = vm.wait_to_schedule[0].works[0]
                # 设置假负载哨兵，（尝试）减少额外逻辑判断
                vm.last_net = Workload.dummy()
                # 移除第一个元素
                # 我们发现了第一个机会窗口
                if is_coop(vm.wait_to_schedule[0]):
                    this_works_num -= 1
                    vm.last_net = vm.wait_to_schedule[0].works[1]
                    vm.ow.append(
                        OpputunityWindow(
                            front=[vm.last_cpu, vm.last_net],
                            rear=[
                                vm.wait_to_schedule[0].works[6], vm.wait_to_schedule[0].works[5]],
                        ))
                vm.wait_to_schedule = list(
                    reversed(vm.wait_to_schedule[1:]))   # 倒转待调度任务，方便后续弹出
            # for task in vm.wait_to_schedule:
            else:
                # if not is_coop(task):
                task = vm.wait_to_schedule.pop()
                assert task == tres.task
                # 独立任务插入一个负载
                # 协作任务插入两个负载
                first_inserted = False
                # 尝试将第一个负载插入机会窗口
                first_ow_ind = 0
                for ow in vm.ow:
                    first_ow_ind += 1
                    # 待插入任务的CPU结束时间
                    ft1 = ow.front[0].finish_time + task.works[0].TIME
                    # 若为独立任务，网络结束时间是机会窗口front的结束时间
                    ft2 = ow.front[1].finish_time
                    if is_coop(task):
                        # 若为协作任务，网络结束时间增加协作任务传输时间
                        ft2 += task.works[1].TIME
                    # 若窗口末尾开始时间晚于当前任务完成时间，则可插入任务
                    if ow.rear[0].start_time > ft1 and ow.rear[1].start_time > ft2:
                        # 向机会窗口加入任务
                        # 独立任务成功插入，可以退出了，但是这里是双循环内，因此我们设置一个flag
                        task.works[0].add_dependency(ow.front[0])
                        this_works_num -= 1
                        # 更新机会窗口的范围
                        ow.front[0] = task.works[0]
                        if is_coop(task):
                            # 为网络任务增加资源依赖
                            this_works_num -= 1
                            task.works[1].add_dependency(ow.front[1])
                            ow.front[1] = task.works[1]
                        # 设置flag，表示任务成功插入
                        first_inserted = True
                        break
                    else:
                        ow.left_try -= 1
                # 清除尝试失败多次的机会窗口
                while len(vm.ow) > 0 and vm.ow[0].left_try <= 0:
                    # print(f'清除{vm}的窗口{vm.ow[0]}')
                    vm.ow.popleft()
                # 让我们处理无法插入的情况
                if not first_inserted:
                    # 将CPU任务依赖与队尾的负载
                    this_works_num -= 1
                    task.works[0].add_dependency(vm.last_cpu)
                    # 更新虚拟机末尾任务是处理任务（独立）
                    vm.last_cpu = task.works[0]
                    if is_coop(task):
                        this_works_num -= 3
                        # 末尾任务是验证任务，无需增加网络依赖，因为网络依赖与CPU
                        vm.last_net = task.works[5]
                        vm.last_cpu = task.works[6]
                        # 产生新的机会窗口
                        vm.ow.append(
                            OpputunityWindow(
                                front=[vm.last_cpu, vm.last_net],
                                rear=[task.works[6], task.works[5]],
                            ))
                    # 若插入队尾，那么就不需要插入第二个任务了，跳出任务分配循环
                    continue
                elif not is_coop(task):
                    # 独立任务已经可以结束了，协作任务还需插入第二个任务
                    continue

                second_inserted = False
                # 别问下边有啥用，下边不影响实验结果
                # 需要保证加密和验证不在同一个机会窗口，以免依赖冲突
                # q_ind = first_ow_ind
                # # for ow in vm.ow[first_ow_ind:]:
                # while q_ind < len(vm.ow):
                # ow = vm.ow[q_ind]
                # q_ind += 1
                # 待插入任务的CPU结束时间, 或者验证任务最晚的完成时间
                # st1 = max(ow.front[0].finish_time +
                #           task.works[0].TIME, task.works[0].finish_time)
                # ft2 = max(ow.front[1].finish_time +
                #           task.works[0].TIME, task.works[0].finish_time)
                # 若窗口末尾开始时间晚于当前任务完成时间，则可插入任务
                #     if ow.rear[0].start_time > ft1 and ow.rear[1].start_time > ft2:
                #         this_works_num -= 2
                #         # 向机会窗口加入任务
                #         task.works[0].add_dependency(ow.front[0])
                #         # 更新机会窗口的范围
                #         ow.front[0] = task.works[0]
                #         # 为网络任务增加资源依赖
                #         task.works[1].add_dependency(ow.front[1])
                #         ow.front[1] = task.works[1]
                #         # 设置flag，表示任务成功插入
                #         second_inserted = True
                #         break
                #     else:
                #         ow.left_try -= 1
                # # 清除尝试失败多次的机会窗口
                # while len(vm.ow) > 0 and vm.ow[0].left_try <= 0:
                #     print(f'清除{vm}的窗口{vm.ow[0]}')
                #     vm.ow.popleft()
                # 若插入失败
                # if not second_inserted:
                this_works_num -= 2
                # 将CPU任务插入队尾，CPU依赖网络任务，因此不用增加依赖
                vm.last_cpu = task.works[5]
                # 网络任务插入队尾
                task.works[1].add_dependency(vm.last_net)
                vm.last_net = task.works[0]
                # assert this_works_num == 0, f'aaaa:{this_works_num}'
                all_works_num -= len(tres.task.works)
            # else:
            #     raise RuntimeError(f'task.work: {task.work}')

        assert vm_first_works_num == 0, '有虚拟机没分配初始任务'
        coop_cnt = sum(1 for t_res in task_results if t_res.is_coop)
        standa_cnt = len(task_results) - coop_cnt
        assert d == 0, f'有{all_works_num}个负载没分配顺序, {coop_cnt}个协作任务，{standa_cnt}个独立任务'
        return [t_res.task.works for t_res in task_results]


if __name__ == '__main__':
    # test_security_objective()
    pass
