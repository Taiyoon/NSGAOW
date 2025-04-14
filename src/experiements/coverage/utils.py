from typing import Type
from platypus.core import Algorithm, Problem
from platypus.extensions import SaveResultsExtension
import os

from platypus.io import load_objectives
from solver.nsgaow import Hyb2

NFE = 100000


def coverage_experment(alg: Type[Algorithm], prob: Type[Problem], nfe: int = 1000, ce: bool = False):
    print(f'start {alg}{prob}{nfe}')
    problem = prob(conf_path='config/base.yml')
    algorithm = alg(problem)
    os.makedirs(
        f'results/{type(algorithm).__name__}_{type(algorithm.problem).__name__}', exist_ok=True)
    # plot 100 points
    # times = nfe // 100
    
    algorithm.add_extension(SaveResultsExtension(
        "results/{algorithm}_{problem}/{nfe}.json", frequency=nfe // 100))
    algorithm.run(nfe)

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

def run_python_file(file_path):
    """运行指定的 Python 文件"""
    try:
        print(f"Running {file_path}...")
        subprocess.run(["python", file_path], check=True)
        print(f"Finished {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {file_path}: {e}")

def main():
    os.chdir('src/experiements/coverage')
    # 获取当前目录下的所有文件
    current_dir = os.getcwd()
    all_files = os.listdir(current_dir)

    # 过滤出符合条件的 Python 文件
    python_files = [f for f in all_files if f.endswith(".py")]
    print("Python files found:", python_files)

    # 并行运行这些文件
    with ThreadPoolExecutor() as executor:
        executor.map(run_python_file, python_files)

if __name__ == "__main__":
    # main()
    ...