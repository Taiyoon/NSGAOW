import logging
from typing import Iterable
from platypus.algorithms import GeneticAlgorithm
from platypus.core import Problem
from platypus.types import Real
from simenv.world import WorldHybridOffline
from solver.encdec import RawNSGA2Encoder


class SPGAEncoder(RawNSGA2Encoder):
    def deadline_and_util(self, indivual: Iterable[float]) -> float:
        r = self.obj_func.multi_objective(
            *self.decode_sequence(indivual), ['sat_ddl_cnt', 'priv_utils'])
        # r = self.obj_func.multi_objective(*self.decode_sequence(indivual), ['makespan', 'security', 'cost'])
        # ans = r[0] * 0.6 + r[1] * 0.3 + r[2] * 0.2
        assert len(r) == 2
        ans = r[0] + r[1]
        return ans


class HybSPGA(Problem):
    '''
    Generic problem
    '''

    def __init__(self, conf_path: str = 'config/base.yml'):
        world = WorldHybridOffline({}, conf_path)
        encoder = SPGAEncoder(world)
        self.encoder = encoder
        li = list(Real(0, 1) for _ in encoder.encode_sequence())
        super().__init__(len(li), 1)
        self.types[:] = li

    def evaluate(self, solution):
        encoder = self.encoder
        x = solution.variables[:]
        solution.objectives[:] = [encoder.deadline_and_util(x), ]


class SPGA(GeneticAlgorithm):
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    problem = HybSPGA()
    algorithm = SPGA(problem)
    algorithm.run(2000)
