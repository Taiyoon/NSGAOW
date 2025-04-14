from typing import Dict, List, Tuple

import numpy as np
from simenv.world import WorldHybridOffline
from solver.encdec import WorldEnDecoder


class HybHeu:
    '''
    improved problem encoding for nsgaow only,
    idk any other solver could tackle this problem
    '''

    def __init__(self, conf_path: str | dict):
        world = WorldHybridOffline({'stdout'}, conf_path)
        self.encoder = WorldEnDecoder(world, world._rng)
        seq = self.encoder.encode_sequence()
        tasks_num = self.encoder._ind_info['Z_offload']['len']

    def evaluate(self, solution: List[int]):
        x: list = solution.variables[:]
        offload = x.pop()
        x += [int(n) for n in offload]
        solution.objectives[:] = list(a for a in self.encoder.three_obj(x))


EPSILON = 1e-6


class MaxCAMin:
    def __init__(self, problem: HybHeu):
        self.problem = problem
        self.finish = False
        self.objectives = None
        self.pop = None
    
    def to_dict(self):
        assert self.finish
        return {
            'algorithm': type(self).__name__,
            'problem': type(self.problem).__name__,
            'pop': [int(n) for n in self.pop],
            'Makespan': self.objectives[0],
            'Security': self.objectives[1],
            'Cost': self.objectives[2]
        }
# ['Makespan'], res['Security'], res['Cost']
    def run(self, delta=0.1):
        assert self.finish == False
        encoder = self.problem.encoder
        task = encoder.task
        # data = encoder.data
        priv = encoder.priv_vm
        pub = encoder.pub_vm
        pub_cpu = np.array([vm.CPU for vm in pub])
        priv_cpu = np.array([vm.CPU for vm in priv])
        priv_time = np.zeros(len(priv), np.float64)
        pub_time = np.zeros(len(pub), np.float64)
        pub_cost = np.zeros(len(pub), np.float64)
        # id, priv, pub, coop, cost
        wait_task = {i: [0, 0, 0, 0.] for i, _ in enumerate(task)}
        # data_result = [[i, -1] for i in range(data)]
        bandwidth = encoder.bandwidth
        delay = encoder.propagation_delay
        task_result = {}
        # max_pub_cpu = max(vm.CPU for vm in pub)
        while len(wait_task) > 0:
            min_pub_time = np.min(pub_time)
            for ind in wait_task.keys():
                dsize = task[ind].DATA.SIZE
                proc = dsize * task[ind].compute_intensity
                pt1 = priv_time + proc / priv_cpu
                std = np.std(
                    np.concat((priv_time, pub_time))
                )
                min_priv = np.min(pt1) + delta*std
                # 要从这里改，我们要选择在标准差范围内负载最高的虚拟机，从而充分利用现有的资源
                sa_priv = np.where(pt1 < min_priv+EPSILON)[0]
                if len(task[ind].DATA.valid_schemes) == 0:
                    priv_ind = np.argmin(pt1)
                    wait_task[ind] = [priv_ind, 0, 0, 0.]
                    continue
                o_enc = task[ind].DATA.valid_schemes[-1].O_ENC
                o_dec = task[ind].DATA.valid_schemes[-1].O_DEC
                net = dsize*1.1 / bandwidth + delay
                pt2 = priv_time + (dsize*o_enc + 0.1*dsize*o_dec) / priv_cpu
                coop_priv = np.argmin(pt2)
                pt_min = pt2[coop_priv]
                ut = np.clip(pub_time, max=pt_min) - pub_time + \
                    (dsize*o_dec + 0.1*dsize*o_enc + proc) / pub_cpu + net
                coop_pub = np.argmin(ut)
                if coop_pub < min_priv and coop_priv < min_priv:
                    wait_task[ind] = [coop_priv, coop_pub,
                                      1, ut[coop_pub]*pub[coop_pub].COST]
                else:
                    wait_task[ind] = [coop_priv, 0, 0, 0.]

            def calc_time(task_ind, result: list):
                priv_ind, pub_ind, is_coop, _ = result
                dsize = task[task_ind].DATA.SIZE
                proc = dsize * task[ind].compute_intensity
                if is_coop <= 0:
                    return proc / priv_cpu[priv_ind], 0.
                else:
                    o_enc = task[task_ind].DATA.valid_schemes[-1].O_ENC
                    o_dec = task[task_ind].DATA.valid_schemes[-1].O_DEC
                    net = dsize*1.1 / bandwidth + delay
                    pt = (dsize*o_enc + 0.1*dsize*o_dec) / \
                        priv_cpu[priv_ind] + net
                    ut = (dsize*o_dec + 0.1*dsize*o_enc + proc) / \
                        pub_cpu[pub_ind] + net
                    return pt, ut
            # max time
            # min cost
            ind, result = min(wait_task.items(), key=lambda item: item[1][-1])
            # update
            task_result[ind] = result[:-1]
            wait_task.pop(ind)
            priv_ind, pub_ind, _, ut = result
            pt, ut = calc_time(ind, result)
            priv_time[priv_ind] += pt
            pub_time[pub_ind] += ut
            pub_cost[pub_ind] += ut
        assert len(wait_task) == 0
        assert len(task_result) == len(task)
        X, Y, Z_off = [], [], []
        for ind, (x, y, off) in sorted(task_result.items()):
            X.append(x)
            Y.append(y)
            Z_off.append(off)
        pop_range: Dict[str, List[Tuple[int, int]]] = encoder.sep_pop(
            encoder.encode_sequence())
        Z_enc = [np.random.randint(low, high)
                 for low, high in pop_range['Z_enc']]
        self.pop = X+Y+Z_enc+Z_off
        self.objectives = encoder.three_obj(self.pop)
        self.finish = True


if __name__ == '__main__':
    problem = HybHeu('config/base.yml')
    solver = MinCAMin(problem)
    solver.run(0.15)
    print(solver.objectives)
