import json
import numpy as np
from simenv.config_parser import ConfigParser
from solver.mincamin import HybHeu, MinCAMin


def run():
    CONF_FILE = 'config/enc_ovhd.yml'
    conf = ConfigParser(CONF_FILE).config
    if isinstance(conf, dict):
        for k, v in conf.items():
            problem = HybHeu(conf_path=v)
            algorithm = MinCAMin(problem)
            algorithm.run(0.15)
            # save_json(f'results/task_amount/{type(problem).__name__}_{k}_{type(algorithm).__name__}.json', algorithm)
            result = algorithm.to_dict()
            # r = result[np.argmax([r.objectives[0] for r in result])]
            # res = {'Solution': str(r)}
            # res['Makespan'], res['Security'], res['Cost'] = problem.encoder.three_obj(r.variables[:])
            with open(f'results/enc_ovhd/{type(problem).__name__}_{k}_{type(algorithm).__name__}.json', 'w') as f:
                json.dump(result, f)


if __name__ == '__main__':
    run()
