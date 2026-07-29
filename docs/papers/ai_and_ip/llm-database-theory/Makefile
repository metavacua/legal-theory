SRCS      := $(wildcard src/0*.xml)
TEX_OUTS  := $(patsubst src/%.xml,generated/%.tex,$(SRCS))
PDF_OUTS  := $(patsubst src/%.xml,generated/%.pdf,$(SRCS))

# Validation and HTML5 generation are NOT paper-specific -- every DocBook
# article in the corpus, this paper included, is validated and built to
# HTML by the single uniform pipeline in .github/workflows/build-corpus.yml
# (jing against the real DocBook 5.2 grammar, this project's DCTERMS
# completeness policy check, then xsltproc docs/xsl/html5.xsl). This
# Makefile only exists for the one thing that genuinely is unique to this
# document: LaTeX/PDF output, which nothing else in the corpus produces.

.PHONY: latex pdf clean

# ── LaTeX ────────────────────────────────────────────────────────────────────

latex: $(TEX_OUTS)

generated/%.tex: src/%.xml ../../../xsl/latex.xsl | generated
	xsltproc --xinclude ../../../xsl/latex.xsl $< > $@
	@echo "==> generated/$*.tex"

# ── PDF (requires pdflatex) ──────────────────────────────────────────────────

pdf: $(PDF_OUTS)

generated/%.pdf: generated/%.tex
	cd generated && pdflatex -interaction=nonstopmode $*.tex
	@echo "==> generated/$*.pdf"

# ── Directories / Cleanup ────────────────────────────────────────────────────

generated:
	mkdir -p generated

clean:
	rm -f generated/*.tex generated/*.pdf
	rm -f generated/*.aux generated/*.log generated/*.out generated/*.toc

# ── Convenience shortcuts ────────────────────────────────────────────────────

.PHONY: open-latex

open-latex: latex
	@f="generated/01-llm-database-theory.tex"; \
	 xdg-open "$$f" 2>/dev/null || open "$$f" 2>/dev/null || echo "Open: $$f"
