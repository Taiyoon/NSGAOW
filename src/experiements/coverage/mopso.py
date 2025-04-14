from utils import NFE, coverage_experment
from platypus.algorithms import SMPSO
from solver.platmo import Hyb1


def run():
    coverage_experment(SMPSO, Hyb1, NFE)


if __name__ == '__main__':
    run()
