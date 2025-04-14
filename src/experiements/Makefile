SUBDIRS = data_size enc_ovhd min_secu task_amount
JOBS ?= 16

all: $(SUBDIRS)

# 声明子目录间的依赖（示例）
# dir1: dir2

$(SUBDIRS):
	$(MAKE) -C $@ -j$(JOBS)

.PHONY: all $(SUBDIRS)