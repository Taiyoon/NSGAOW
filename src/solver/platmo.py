from functools import partial
import logging

from matplotlib import pyplot as plt
from platypus import NSGAII, Problem, Real, Hypervolume, calculate, experiment, display,  SMPSO, SPEA2, OMOPSO

from simenv.world import WorldHybridOffline
from solver.encdec import RawNSGA2Encoder


class Hyb1(Problem):
    '''
    Generic problem
    '''
    def __init__(self, conf_path: str = 'config/base.yml'):
        world = WorldHybridOffline({}, conf_path)
        encoder = RawNSGA2Encoder(world)
        self.encoder = encoder
        li = list(Real(0, 1) for low, high in encoder.encode_sequence())
        super().__init__(len(li), 3)
        self.types[:] = li

    def evaluate(self, solution):
        encoder = self.encoder
        x = solution.variables[:]
        solution.objectives[:] = list(a for a in encoder.three_obj(x))

class Hyb3(Problem):
    def __init__(self, conf_path: str = 'config/base.yml'):
        world = WorldHybridOffline({}, conf_path)
        encoder = RawNSGA2Encoder(world)
        self.encoder = encoder
        li = list(Real(0, 1) for low, high in encoder.encode_sequence())
        super().__init__(len(li), 2)
        self.types[:] = li

    def evaluate(self, solution):
        encoder = self.encoder
        x = solution.variables[:]
        solution.objectives[:] = list(a for a in encoder.two_obj(x))
    


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    algorithms = [(OMOPSO, {"epsilons": [0.1]}), NSGAII, SMPSO, SPEA2]
    problems = [Hyb1]

    results = experiment(algorithms, problems, nfe=10000, seeds=1, display_stats=True, )

    hyp = Hypervolume(minimum=[0, 0, 0], maximum=[639, 2155, 2])
    hyp_result = calculate(results, hyp)
    display(hyp_result, ndigits=3)

    fig = plt.figure()

    for i, algorithm in enumerate(results.keys()):
        result = results[algorithm]["Hyb1"][0]

        ax = fig.add_subplot(2, 5, i+1, projection='3d')
        ax.scatter([s.objectives[0] for s in result],
                   [s.objectives[1] for s in result],
                   [s.objectives[2] for s in result])
        ax.set_title(algorithm)
        ax.view_init(elev=30.0, azim=15.0)
        ax.locator_params(nbins=4)

    plt.show()
