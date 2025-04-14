import os
from typing import List

import numpy as np

from platypus.core import Solution
from platypus.io import load_json


def pesudo_weight_choose(results: List[list], w: List[float]) -> List[float]:
    arr = np.array(results)
    assert arr.shape[1] == 3
    norm_arr = (arr - arr.min(0)) / (arr.max(0) - arr.min(0))
    assert all(n >= 0. and n <= 1. for n in w)
    # 权重越大，需要选择越小的值
    n_w = 1. - np.array(w)
    return results[np.argmin(np.sum(
        (norm_arr - n_w)**2, axis=1
    ))]


def improved_pwc(results: List[list], w: List[float]) -> List[float]:
    arr = np.array(results)
    assert arr.shape[1] == 3
    arr = arr[:, :2]
    norm_arr = (arr - arr.min(0)) / (arr.max(0) - arr.min(0))
    assert all(n >= 0. and n <= 1. for n in w)
    # 权重越大，需要选择越小的值
    n_w = 1. - np.array(w)[:2]
    return results[np.argmin(np.sum(
        (norm_arr - n_w)**2, axis=1
    ))]


def main():
    folder_path = 'results/task_amount/'
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)  # 文件的完整路径
            result = load_json(file_path)
            t_str = file.split('_')[1]
            assert t_str.startswith('task')
            task_num = int(t_str[4:])
            # 完工时间优先
            print(task_num)
            print(pesudo_weight_choose(
                list(r.objectives for r in result), [0.8, 0.2, 0.]))


if __name__ == '__main__':
    main()
