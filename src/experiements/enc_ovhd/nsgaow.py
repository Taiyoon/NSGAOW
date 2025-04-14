from platypus.io import save_json
from simenv.config_parser import ConfigParser
from solver.nsgaow import NSGAOW, Hyb2
from solver.platmo import Hyb1

def run():
    CONF_FILE = 'config/enc_ovhd.yml'
    conf = ConfigParser(CONF_FILE).config
    if isinstance(conf, dict):
        for k, v in conf.items():
            problem = Hyb1(conf_path=v)
            algorithm = NSGAOW(problem)
            algorithm.run(1000000)
            save_json(f'results/enc_ovhd/{type(problem).__name__}_{k}_{type(algorithm).__name__}.json', algorithm)
    
if __name__ == '__main__':
    run()