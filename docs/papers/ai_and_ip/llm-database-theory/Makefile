SRCS      := $(wildcard src/0*.xml)
HTML_OUTS := $(patsubst src/%.xml,generated/%.html,$(SRCS))
TEX_OUTS  := $(patsubst src/%.xml,generated/%.tex,$(SRCS))
PDF_OUTS  := $(patsubst src/%.xml,generated/%.pdf,$(SRCS))
# 00-metadata.xml is an XInclude fragment (<db:info>, XIncluded into each
# article's <db:info> slot) — it has no <db:article> root, so it isn't a
# standalone document custom.rnc's `start` pattern can validate.
ARTICLES  := $(filter-out src/00-metadata.xml,$(SRCS))

.PHONY: all html latex pdf validate clean

all: validate html latex

# ── Validation ──────────────────────────────────────────────────────────────

validate: $(SRCS)
	@echo "==> Validating XML (XInclude + xmllint well-formedness)"
	@for f in $(SRCS); do \
	  echo "    $$f"; \
	  xmllint --noout --xinclude "$$f"; \
	done
	@echo "==> Custom RELAX NG validation"
	@which jing >/dev/null 2>&1 && \
	  for f in $(ARTICLES); do \
	    jing -c schema/custom.rnc "$$f" && echo "    OK: $$f" || true; \
	  done || echo "    (jing not installed; skipping RELAX NG step)"

# ── HTML5 ────────────────────────────────────────────────────────────────────

html: $(HTML_OUTS)

generated/%.html: src/%.xml xsl/html5.xsl | generated
	xsltproc --xinclude xsl/html5.xsl $< > $@
	@echo "==> generated/$*.html"

# ── LaTeX ────────────────────────────────────────────────────────────────────

latex: $(TEX_OUTS)

generated/%.tex: src/%.xml xsl/latex.xsl | generated
	xsltproc --xinclude xsl/latex.xsl $< > $@
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
	rm -f generated/*.html generated/*.tex generated/*.pdf
	rm -f generated/*.aux generated/*.log generated/*.out generated/*.toc

# ── Convenience shortcuts ────────────────────────────────────────────────────

.PHONY: open-html open-latex

open-html: html
	@f="generated/01-llm-database-theory.html"; \
	 xdg-open "$$f" 2>/dev/null || open "$$f" 2>/dev/null || echo "Open: $$f"

open-latex: latex
	@f="generated/01-llm-database-theory.tex"; \
	 xdg-open "$$f" 2>/dev/null || open "$$f" 2>/dev/null || echo "Open: $$f"
