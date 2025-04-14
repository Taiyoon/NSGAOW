# 查找当前目录下的所有 .py 文件
PY_FILES := $(wildcard *.py)
WORKPATH := ../../../

# 定义目标路径
PATH := src/experiements/enc_ovhd

# 虚拟环境的激活脚本路径（Linux）
VENV_ACTIVATE := .venv/Scripts/activate

# 默认任务
all: run_scripts

# 任务：并行运行当前目录下的所有 .py 文件
run_scripts: $(PY_FILES)
	@echo "Running all .py files in the $(PATH) directory in parallel..."
	@cd $(WORKPATH) && source $(VENV_ACTIVATE) && echo $(PY_FILES) | tr ' ' '\n' | xargs -n 1 -P 16 -I {} python $(PATH)/{}


# 任务：清理虚拟环境
clean:
	@echo "Cleaning up..."
	@rm -rf __pycache__

.PHONY: all run_scripts clean venv