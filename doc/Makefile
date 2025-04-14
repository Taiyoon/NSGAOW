# GB18030 encoded
# Makefile for converting Markdown files to Markdown using Pandoc

# Variables
PANDOC = pandoc
INPUT = draft.md
OUTPUT = draft.docx
LATEX_OUTPUT = draft.tex
TEMPLATE = ./templates/templates_±ÍÃ‚±‡∫≈.docx
BIBTEX = ../thesis/test.bib 

# Default target
all: $(OUTPUT)

# Rule to convert markdown to docx
# pandoc --reference-doc templates.docx -s exp2.md -o output.docx
$(OUTPUT): $(INPUT) $(BIBTEX)
	$(PANDOC) --reference-doc $(TEMPLATE) --bibliography $(BIBTEX) -s $(INPUT) -o $(OUTPUT) --citeproc --csl china-national-standard-gb-t-7714-2015-numeric.csl

# Clean up generated files
clean:
	rm -f $(OUTPUT)

latex:
	$(PANDOC) --reference-doc $(TEMPLATE) --bibliography $(BIBTEX) -s $(INPUT) -o $(LATEX_OUTPUT) --citeproc --csl china-national-standard-gb-t-7714-2015-numeric.csl

.PHONY: all clean latex