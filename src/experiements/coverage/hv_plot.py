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

    matplotlib.get_cachedir()
    # 设置全局字体（推荐使用开源字体）
    # 修复样式声明中的中文逗号错误
    plt.style.use(['science', 'cjk-sc-font', 'no-latex', 'ieee'])  # 使用英文逗号
    font = FontProperties(fname="C:/Windows/Fonts/STSONG.TTF")  # 黑体常规
    plt.rcParams['font.family'] = 'SimSun'  # 使用黑体，或者指定具体字体文件路径
    plt.rcParams['font.serif'] = ['SimSun']  # 指定支持的字体列表
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 创建画布 (75mm = 2.95英寸，按4:3比例设置高度)
    plt.subplots(figsize=(3, 3*(3/4)))  # 宽度75mm，高度按3:4比例
    THESIS_PATH = 'thesis/img/'    
    data = {}
    METHODS = ['NSGAOW', 'NSGAII', 'SMPSO', 'SPEA2']
    for method in METHODS:
        problem_name = 'Hyb' + str(1+int(method == 'NSGAOWx'))
        folder_path = f"results/{method}_{problem_name}"  # 替换为你的文件夹路径
        ref_set = load_objectives("results/Hyb1_1000000NFE.pf")
        # gd_calc = GenerationalDistance(reference_set=ref_set)
        hv_calc = Hypervolume(reference_set=ref_set)
        
        print('load')
        _nums = 0
        for root, dirs, files in os.walk(folder_path):
            max_nfe = 0
            for file in files:
                nfe = int(file.split('.')[0])
                max_nfe = max(max_nfe, nfe)
                # _nums += 1
                # print(_nums)
                # print(file)
            file_path = os.path.join(root, str(max_nfe)+'.json')  # 文件的完整路径
            result = load_json(file_path)
            hv = hv_calc.calculate(result)
            # d = data.setdefault(method, {})
            print(f'alg:{method}, hv: {hv}, nfe:{max_nfe}')
            data[method] = hv
    print('loaded')
    pprint(data)

    # folder_path = f"results/hypervolume"  # 替换为你的文件夹路径
    # ref_set = load_objectives("results/Hyb1_10000NFE.pf")
    # hv_calc = Hypervolume(reference_set=ref_set)

    # for root, dirs, files in os.walk(folder_path):
    #     for file in files:
    #         alg_name = file.split('_')[1].split('.')[0]
    #         file_path = os.path.join(root, file)  # 文件的完整路径
    #         result = load_json(file_path)
    #         hv = hv_calc.calculate(result)
    #         data[alg_name] = hv

    x, y = [], []
    for name, v in data.items():
        x.append(name)
        y.append(v)

    # 创建一个柱状图
    plt.bar(x, y, 0.25)
    plt.ylabel("超体积指标")
    plt.savefig(THESIS_PATH+'hv.pdf', format='pdf', dpi=300, bbox_inches='tight')
    # 显示图形
    plt.show()


if __name__ == '__main__':
    plot()
