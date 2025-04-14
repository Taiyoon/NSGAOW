import copy
import random
from platypus.algorithms import EpsNSGAII
from platypus.core import Variator
from platypus.indicators import GenerationalDistance
from platypus import DTLZ2, NSGAII, Hypervolume, load_objectives
import matplotlib.pyplot as plt
import logging
from platypus import AbstractGeneticAlgorithm, NSGAII, Problem, experiment, Hypervolume, calculate, display, PlatypusConfig, RandomGenerator, TournamentSelector, nondominated_sort, Integer, nondominated_truncate

from platypus.io import save_json
from platypus.operators import HUX, SPX, SSX, BitFlip, GAOperator
from platypus.types import Binary
from simenv.config_parser import ConfigParser
from simenv.world import WorldHybridOffline
from solver.encdec import WorldEnDecoder
from solver.platmo import Hyb1


class Hyb2(Problem):
    '''
    improved problem encoding for nsgaow only,
    idk any other solver could tackle this problem
    '''

    def __init__(self, conf_path: str | dict):
        world = WorldHybridOffline({}, conf_path)
        self.encoder = WorldEnDecoder(world, world._rng)
        seq = self.encoder.encode_sequence()
        tasks_num = self.encoder._ind_info['Z_offload']['len']
        # 使用整数表示虚拟机
        # 使用格雷码表示数据安全策略选择方案
        li = list(Integer(low, high)
                  for low, high in seq[:-tasks_num])
        # 使用二进制表示卸载方案
        li = li + [Binary(1) for _ in range(tasks_num)]
        # li.append(Binary(tasks_num))
        super().__init__(len(li), 3)
        self.types[:] = li

    def evaluate(self, solution):
        x: list = solution.variables[:]
        # offload = x.pop()
        # x += [int(n) for n in offload]
        for i in range(len(x)):
            if isinstance(x[i], list):
                x[i] = int(x[i][0])
        solution.objectives[:] = list(a for a in self.encoder.three_obj(x))


hux = HUX()


class OnePoint(Variator):

    def __init__(self, probability=1.0):
        super().__init__(2)
        self.probability = probability

    def evolve(self, parents):
        result1 = copy.deepcopy(parents[0])
        result2 = copy.deepcopy(parents[1])
        problem = result1.problem
        pl = problem.nvars
        a = random.randint(0, pl)
        if random.uniform(0.0, 1.0) <= self.probability:
            p1 = result1.variables[a:]
            result1.variables[:] = result1.variables[:a] + \
                result2.variables[a:]
            result1.evaluated = False
            result2.variables[:] = result2.variables[:a] + p1
            result2.evaluated = False
        else:
            return hux.evolve(parents)
            # for i in range(problem.nvars):
            #     if isinstance(problem.types[i], Binary):
            #         for j in range(problem.types[i].nbits):
            #             if result1.variables[i][j] != result2.variables[i][j]:
            #                 if bool(random.getrandbits(1)):
            #                     result1.variables[i][j] = not result1.variables[i][j]
            #                     result2.variables[i][j] = not result2.variables[i][j]
            #                     result1.evaluated = False
            #                     result2.evaluated = False

        return [result1, result2]


# variator = BitFlip(0.02)
variator = BitFlip(0.02)
# crossover = OnePoint(0.5)
crossover = OnePoint(0.5)
opeartor = GAOperator(crossover, variator)


class NSGAOW(AbstractGeneticAlgorithm):
    def __init__(self, problem,
                 population_size=100,
                 generator=RandomGenerator(),
                 selector=TournamentSelector(2),
                 variator=opeartor,
                 archive=None,
                 **kwargs):
        super().__init__(problem, population_size, generator, **kwargs)
        self.selector = selector
        self.variator = variator
        self.archive = archive  # 应该初始化的状态

    def step(self):
        if self.nfe == 0:
            self.initialize()
        else:
            self.iterate()

        if self.archive is not None:
            self.result = self.archive
        else:
            self.result = self.population

    def initialize(self):
        super().initialize()

        if self.archive is not None:
            self.archive += self.population

        if self.variator is None:
            # 根据个体的第一个编码选择variator
            self.variator = PlatypusConfig.default_variator(self.problem)

    def iterate(self):
        offspring = []

        # 从上一代种群中选取两个个体进化，产生新的population_size个个体
        while len(offspring) < self.population_size:
            parents = self.selector.select(
                self.variator.arity, self.population)
            offspring.extend(self.variator.evolve(parents))

        self.evaluate_all(offspring)

        # 将新种群与原种群合并，以精英保留
        offspring.extend(self.population)
        nondominated_sort(offspring)
        # 根据优先级与拥挤度选取前pop_size个个体
        self.population = nondominated_truncate(
            offspring, self.population_size)

        # 暂时还不清楚archive是干嘛的，应该没用
        if self.archive is not None:
            self.archive.extend(self.population)


class NSGAOW(EpsNSGAII):
    def __init__(self, problem, epsilons=0.01, population_size=100, generator=RandomGenerator(), selector=TournamentSelector(2), variator=None, **kwargs):
        super().__init__(problem, epsilons, population_size, generator, selector, variator, **kwargs)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    CONF_FILE = 'config/task_amount.yml'
    conf = ConfigParser(CONF_FILE).config
    if isinstance(conf, dict):
        for k, v in conf.items():
            problem = Hyb1(conf_path=v)
            algorithm = NSGAOW(problem)
            algorithm.run(2000)
            save_json(
                f'results/task_amount/{type(problem).__name__}_{k}_{type(algorithm).__name__}.json', algorithm)
            # print(algorithm.result)

    # # Collect the population at each generation.
    # results = {}
    # algorithm.run(1000, callback=lambda a: results.update(
    #     {a.nfe: {"population": a.result}}))

    # # Compute the hypervolume at each generation.
    # ref_set = load_objectives("results/Hyb1_10000NFE.pf", problem)
    # # hyp = Hypervolume(reference_set=ref_set)
    # # hyp = GenerationalDistance(reference_set=ref_set)
    # # hyp = Hypervolume(ref_set)
    # gd = GenerationalDistance(reference_set=ref_set)

    # for nfe, data in results.items():
    #     data["hypervolume"] = gd.calculate(data["population"])

    # # Plot the results using matplotlib.
    # plt.plot(results.keys(),
    #          [x["hypervolume"] for x in results.values()])
    # plt.xlabel("NFE")
    # plt.ylabel("Hypervolume")
    # plt.show()
