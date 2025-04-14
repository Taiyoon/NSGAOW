from utils import NFE, coverage_experment
from platypus.algorithms import NSGAII
from solver.platmo import Hyb1


def run():
    coverage_experment(NSGAII, Hyb1, NFE)


if __name__ == '__main__':
    run()
