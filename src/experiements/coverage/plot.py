# plot gd
from pprint import pprint
import matplotlib
import matplotlib.pyplot as plt
from platypus.indicators import GenerationalDistance, Hypervolume, InvertedGenerationalDistance
from platypus.io import load_json, load_objectives
import matplotlib.font_manager
import os


from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
import scienceplots
import numpy as np

# if __name__ == '__main__':


def plot():
    # 修复样式声明中的中文逗号错误
    plt.style.use(['science', 'cjk-sc-font', 'no-latex', 'ieee'])  # 使用英文逗号

    # 创建画布 (75mm = 2.95英寸，按4:3比例设置高度)
    # fig, ax =
    plt.subplots(figsize=(3, 3*(3/4)))  # 宽度75mm，高度按3:4比例
    THESIS_PATH = 'thesis/img/'

    matplotlib.get_cachedir()
    # 设置全局字体（推荐使用开源字体）

    font = FontProperties(fname="C:/Windows/Fonts/SimSun.ttc")  # 黑体常规
    plt.rcParams['font.family'] = 'SimSun'  # 使用黑体，或者指定具体字体文件路径
    plt.rcParams['font.serif'] = ['SimSun']  # 指定支持的字体列表
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    METHODS = ['NSGAOW', 'NSGAII', 'SMPSO', 'SPEA2']
    # , 'SMPSO', 'NSGAII', 'NSGAIII',
    # 'SMPSO', 'SPEA2'
    data = {}
    for method in METHODS:
        problem_name = 'Hyb' + str(1+int(method == 'NSGAOWx'))
        folder_path = f"results/{method}_{problem_name}"  # 替换为你的文件夹路径
        ref_set = load_objectives("results/Hyb1_1000000NFE.pf")
        gd_calc = InvertedGenerationalDistance(reference_set=ref_set)
        # gd_calc = GenerationalDistance(reference_set=ref_set)
        # gd_calc = Hypervolume(reference_set=ref_set)
        
        print('load')
        _nums = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # _nums += 1
                # print(_nums)
                # print(file)
                file_path = os.path.join(root, file)  # 文件的完整路径
                result = load_json(file_path)
                gd = gd_calc.calculate(result)
                d = data.setdefault(method, {})
                nfe = int(file.split('.')[0])
                if method == 'NSGAOW':
                    nfe = nfe//3*2
                d[nfe] = gd
    print('loaded')
    pprint(data)
    for name, v in data.items():
        # 提取 x 和 y 数据
        x = sorted(v.keys())  # x 轴数据（按键排序）
        y = [v[key] for key in x]  # y 轴数据
        # 绘制曲线
        plt.plot(x, y,  label=name)
    plt.legend()
    # 添加标题和标签
    plt.xlabel("目标函数评估次数")
    plt.ylabel("反转世代距离")
    plt.savefig(THESIS_PATH+'igd.pdf', format='pdf', dpi=300, bbox_inches='tight')
    # 显示图形
    plt.show()


if __name__ == '__main__':
    plot()
    ...
