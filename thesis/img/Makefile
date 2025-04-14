# 定义变量
DOT_FILES := $(wildcard *.dot)  # 查找所有 .dot 文件
PDF_FILES := $(DOT_FILES:.dot=.svg)  # 将 .dot 文件转换为 .pdf 文件

# 默认目标
all: $(PDF_FILES)

# # 规则：将 .dot 文件转换为 .pdf 文件
# %.pdf: %.dot
# 	@echo "Generating $@ from $<"
# 	dot -Tpdf $< -o $@

# # 规则：将 .dot 文件转换为 .eps 文件
# %.eps: %.dot
# 	@echo "Generating $@ from $<"
# 	dot -Teps $< -o $@

# # 规则：将 .dot 文件转换为 .psd 文件
# %.psd: %.dot
# 	@echo "Generating $@ from $<"
# 	dot -Tps2 $< -o $@

# 规则：将 .dot 文件转换为 .svg 文件
%.svg: %.dot
	@echo "Generating $@ from $<"
#	neato -Tsvg $< -o $@
	dot -Tsvg $< -o $@

# 清理生成的 PDF 文件
clean:
	@echo "Cleaning up..."
	rm -f $(PDF_FILES)

.PHONY: all clean