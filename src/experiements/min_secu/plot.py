import os
from pprint import pprint

from matplotlib import pyplot as plt
import matplotlib
from matplotlib.font_manager import FontProperties
import numpy as np
from platypus.io import load_json
import scienceplots
from solver.result_chooser import pesudo_weight_choose

data = {}


def read():
    folder_path = 'results/min_secu/'
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)  # 文件的完整路径
            result = load_json(file_path)
            t_str = file.split('_')[1]
            assert t_str.startswith('secu')
            task_num = int(t_str[4:])
            alg_name = file.split('_')[2].split('.')[0]
            if alg_name == 'NSGAOW':
                d = data.setdefault('NSGAOW-1', {})
                d[task_num] = pesudo_weight_choose(
                    list(r.objectives for r in result), [0.9, 0.1, 0.])
                d = data.setdefault('NSGAOW-2', {})
                d[task_num] = pesudo_weight_choose(
                    list(r.objectives for r in result), [0.1, 0.9, 0.])
            elif alg_name in {'SPGA', 'MinCAMin'}:
                d = data.setdefault(alg_name, {})
                d[task_num] = result['Makespan'], result['Security'], result['Cost']
            else:
                raise NotImplementedError


def plot(obj: str, show: bool = True):
    assert obj in {'Makespan', 'Security', 'Cost'}
    alg_ind = {
        'Makespan': 0, 'Security': 1, 'Cost': 2}[obj]

    alg_chn = ['完工时间 (s)', '安全性', '成本 ($)'][alg_ind]
    plt.style.use(['science', 'cjk-sc-font', 'no-latex', 'ieee'])  # 使用英文逗号

    # 创建画布 (75mm = 2.95英寸，按4:3比例设置高度)
    # fig, ax =
    THESIS_PATH = 'thesis/img/'
    matplotlib.get_cachedir()
    # 设置全局字体（推荐使用开源字体）
    font = FontProperties(fname="C:/Windows/Fonts/STSONG.TTF")  # 黑体常规
    plt.rcParams['font.family'] = 'SimSun'  # 使用黑体，或者指定具体字体文件路径
    plt.rcParams['font.sans-serif'] = ['SimSun']  # 指定支持的字体列表
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 设置全局字号为 7pt
    plt.rcParams.update({
        'font.size': 7,             # 全局字号
        'axes.titlesize': 7,        # 标题字号
        'axes.labelsize': 7,        # 坐标轴标签字号
        'xtick.labelsize': 7,       # X轴刻度标签字号
        'ytick.labelsize': 7,       # Y轴刻度标签字号
        'legend.fontsize': 7,       # 图例字号
        'figure.titlesize': 7,      # 图标题字号
    })

    # data = {
    #     'MinCAMin': {1: 0.05, 2: 0.05, 3: 0.03},
    #     'NSGAOW-1': {1: 0.24, 2: 0.26, 3: 0.05},
    #     'NSGAOW-2': {1: 0.19, 2: 0.20, 3: 0.03},
    #     'SPGA': {1: 0.36, 2: 0.46, 3: 0.07}
    # }
    # obj_data = {
    #     name: {
    #         scene: values[alg_ind]
    #         for scene, values in scenes.items()
    #     } 
    #         for name, scenes in data.items()
    # }
    obj_data = {}
    for name, scenes in data.items():
        new_scenes = {}
        for scene, values in scenes.items():
            if alg_ind != 1:
                new_scenes[scene] = values[alg_ind]
            else:
                new_scenes[scene] = 1-values[alg_ind]
        obj_data[name] = new_scenes

    FIGSIZE = 3
    algorithms = list(obj_data.keys())
    scenarios = [1, 2, 3]
    bar_width = FIGSIZE/15  # 柱状图宽度
    index = np.arange(len(algorithms))  # 算法分组基准坐标

    # ----------------------------
    # 画图配置
    # ----------------------------

    # 宽度1.9inch，高度按3:4比例
    fig, ax = plt.subplots(figsize=(FIGSIZE, FIGSIZE*(3/4)))

    # 绘制每个场景的柱状图
    for i, scenario in enumerate(scenarios):
        costs = [obj_data[alg][scenario] for alg in algorithms]
        ax.bar(
            index + i * bar_width,  # 控制横向偏移
            costs,
            bar_width,
            label=f'场景 {scenario}'
        )

    # ----------------------------
    # 图形装饰
    # ----------------------------
    # ax.set_xlabel('算法类型')
    # ax.set_ylabel('成本 ($)')
    # ax.set_title('不同算法及场景下的成本对比')
    ax.set_xticks(index + bar_width)
    ax.set_xticklabels(algorithms)
    ax.legend()

    plt.tight_layout()

    # 绘制曲线
    plt.legend()
    # 添加标题和标签
    # plt.xlabel('场景')
    plt.ylabel(alg_chn)
    # 显示图形
    if show:
        plt.show()
    else:
        plt.savefig(THESIS_PATH+f'min_secu_vs_{obj.lower()}.pdf',
                    format='pdf', dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    read()
    pprint(data)
    for obj in {'Makespan', 'Security', 'Cost'}:
        plot(obj, False)
        # plot(obj, True)
        ...
