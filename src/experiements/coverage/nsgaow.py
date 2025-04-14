import os
from utils import NFE, coverage_experment
from platypus.algorithms import NSGAIII
from platypus.extensions import SaveResultsExtension
from solver.nsgaow import NSGAOW, Hyb2
from solver.platmo import Hyb1
# from solver.platmo import Hyb1


def run():
    coverage_experment(NSGAOW, Hyb1, 3*NFE//2)
    # print('临时修正')
    # problem = Hyb1(conf_path='config/base.yml')
    # algorithm = NSGAIII(problem, 12)
    # os.makedirs(
    #     f'results/{type(algorithm).__name__}_{type(algorithm.problem).__name__}', exist_ok=True)
    # # plot 100 points
    # # times = nfe // 100

    # algorithm.add_extension(SaveResultsExtension(
    #     "results/{algorithm}_{problem}/{nfe}.json", frequency=NFE // 1000))
    # algorithm.run(NFE)


if __name__ == '__main__':
    run()
