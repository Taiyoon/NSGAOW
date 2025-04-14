import os
from pprint import pprint

from matplotlib import pyplot as plt
import matplotlib
from matplotlib.font_manager import FontProperties
import numpy as np
from platypus.io import load_json
import scienceplots
from solver.result_chooser import improved_pwc, pesudo_weight_choose

data = {}


def read():
    folder_path = 'results/task_amount/'
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)  # 文件的完整路径
            result = load_json(file_path)
            t_str = file.split('_')[1]
            assert t_str.startswith('task')
            task_num = int(t_str[4:])
            alg_name = file.split('_')[2].split('.')[0]
            if alg_name == 'NSGAOW':
                d = data.setdefault('NSGAOW-1', {})
                d[task_num] = improved_pwc(
                    list(r.objectives for r in result), [0.8, 0.2, 0.0])
                d = data.setdefault('NSGAOW-2', {})
                d[task_num] = improved_pwc(
                    list(r.objectives for r in result), [0.2, 0.8, 0.])
            elif alg_name in {'SPGA', 'MinCAMin'}:
                d = data.setdefault(alg_name, {})
                d[task_num] = result['Makespan'], result['Security'], result['Cost']
            else:
                raise NotImplementedError


def plot(obj: str, show: bool = True):
    '画折线图'
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
    plt.subplots(figsize=(3, 3*(3/4)))  # 宽度3inch，高度按3:4比例

    for alg, v in data.items():
        # 提取 x 和 y 数据
        x = sorted(v.keys())  # x 轴数据（按键排序）
        y = [v[key][alg_ind] for key in x]  # y 轴数据
        # 我们的安全性目标在优化时作为最小化目标处理的
        if obj == 'Security':
            y = [1.-v for v in y]
        plt.plot(x, y,  label=alg, marker='o', markersize=3)
    # pprint(data)
    if obj=='Security':
        plt.ylim(0., 1.05)
    # 绘制曲线
    plt.legend()
    # 添加标题和标签
    plt.xlabel('任务数量（个）')
    plt.ylabel(alg_chn)
    # 显示图形
    if show:
        plt.show()
    else:
        plt.savefig(THESIS_PATH+f'task_amount_vs_{obj.lower()}.pdf',
                    format='pdf', dpi=300, bbox_inches='tight')


def plot_box(obj: str, show: bool = True):
    '画多组的箱形图'
    # 通用设置不要动
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
    plt.style.use(['science', 'cjk-sc-font', 'no-latex', 'ieee'])  # 使用英文逗号
    # 可以调整图像大小
    FIGSIZE = 3
    # 创建画布 (75mm = 2.95英寸，按4:3比例设置高度)
    plt.subplots(figsize=(FIGSIZE, FIGSIZE*(3/4)))  # 宽度3inch，高度按3:4比例
    # 设置柱状图的宽度
    bar_width = FIGSIZE / 15

    # 数据处理
    assert obj in {'Makespan', 'Security', 'Cost'}
    alg_ind = {
        'Makespan': 0, 'Security': 1, 'Cost': 2}[obj]
    alg_chn = ['完工时间 (s)', '安全性', '成本 ($)'][alg_ind]
    # 数据
    groups = ['Alg 1', 'Alg 2', 'Alg 3']
    categories = [100, 200, 300]
    # 每个组在每个类别下的值
    values = {
        'Group 1': [10, 20, 30],
        'Group 2': [15, 25, 35],
        'Group 3': [20, 30, 40]
    }
    groups.clear()
    categories = next(iter(data.values()))
    values.clear()

    pos = np.arange(len(categories))
    for alg, v in data.items():
        # 提取 x 和 y 数据
        if len(categories) == 0:
            categories = sorted(v.keys())  # x 轴数据（按键排序）
        else:
            assert categories == sorted(v.keys()), '数据的x轴不同'
        y = [v[key][alg_ind] for key in x]  # y 轴数据
        # 我们的安全性目标在优化时作为最小化目标处理的
        if obj == 'Security':
            y = [1.-v for v in y]
        # plt.box(x, y,  label=alg)
    pprint(data)

    # 绘制曲线
    plt.legend()
    # 添加标题和标签
    plt.xlabel('任务数量（个）')
    plt.ylabel(alg_chn)
    
    # 显示图形
    THESIS_PATH = 'thesis/img/'
    if show:
        plt.show()
    else:
        plt.savefig(THESIS_PATH+f'task_amount_vs_{obj.lower()}.pdf',
                    format='pdf', dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    read()
    pprint(data)
    for obj in {'Makespan', 'Security', 'Cost'}:
        plot(obj, False)
        # plot(obj, True)
        ...
