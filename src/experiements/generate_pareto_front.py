

from platypus.algorithms import NSGAII, NSGAIII
from platypus.io import load_json, save_json, save_objectives
from solver.nsgaow import NSGAOW, Hyb2
from solver.platmo import Hyb1, Hyb3

def optimal_solution(nfe: int):

    problem = Hyb2('config/base.yml')
    algorithm = NSGAOW(problem)
    algorithm.run(nfe)
    save_json(f"results/Hyb1_{nfe}NFE.json", algorithm, indent=4)

def calc_pareto_front(file: str):
    result = load_json(file)
    for solution in result:
        print(solution.objectives)
    save_objectives(file.split('.')[0]+'.pf', result)


if __name__ == '__main__':
    # optimal_solution(5000)
    calc_pareto_front("results/Hyb1_5000NFE.json")
    
