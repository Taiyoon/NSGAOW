from utils import NFE, coverage_experment
from platypus.algorithms import SPEA2
from solver.platmo import Hyb1


def run():
    coverage_experment(SPEA2, Hyb1, NFE)


if __name__ == '__main__':
    run()
