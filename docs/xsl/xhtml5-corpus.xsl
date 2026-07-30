<?xml version="1.0" encoding="UTF-8"?>
<!--
  xhtml5-corpus.xsl — local customization layer over the vendored
  docbook-xsl-ns xhtml5 stylesheet (xsl:import'd below; this file does
  not fork or duplicate it).

  This corpus is served on GitHub Pages as text/html (see
  .github/workflows/deploy-pages.yml — no header-override mechanism is
  available there), but the raw upstream xhtml5 stylesheet targets real
  XML/XHTML serving semantics. That mismatch produces two corpus-wide
  HTML5 text/html parse errors and lets one upstream vendor bug through,
  confirmed against the Nu Html Checker (vnu.jar) and html5lib under
  real text/html parsing:

    1. Every page opens with a literal "<?xml version=...?>" processing
       instruction. Meaningless, and a hard parse error, under HTML5's
       text/html parsing algorithm (only valid in XML parsing mode).
    2. xml:lang is emitted without a paired lang attribute wherever the
       source document carries @lang/@xml:lang — and the root <html>
       element gets neither, at all. HTML5 text/html parsing requires
       lang/xml:lang to carry the same value when both are present.
    3. (Upstream docbook-xsl-ns bug, not this corpus's own markup —
       xhtml/block.xsl's <blockquote><attribution> table.) Hardcodes the
       HTML *attribute* names "cellspacing"/"cellpadding" — not real
       CSS properties; no such CSS property exists — into an inline
       style attribute.

  Each fix overrides only the specific upstream mechanism responsible,
  relying on xsl:import's ordinary precedence rules: this file is the
  importer, so anything it defines here (by template match/mode/name, or
  by xsl:output attribute) wins over the same-named thing anywhere in
  the imported tree. No generated HTML is ever string-post-processed.
  This is a narrow customization layer, not a reimplementation —
  distinct from, and not a reversion of, the 2026-07-28 retirement of
  this repo's old hand-rolled, 319-line docs/xsl/html5.xsl (see that
  design's own "explicitly out of scope, not precluded" section, which
  anticipates exactly this kind of addition: "any future customization
  layer... as an explicit, separately-scoped addition on top of
  docbook-xsl-ns").

  Full research record (which docbook-xsl-ns file/line each fix targets,
  and why no existing xsltproc stringparam reaches these controls):
  .superpowers/sdd/2026-07-29-xhtml5-text-html-conformance.md
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:d="http://docbook.org/ns/docbook"
    xmlns="http://www.w3.org/1999/xhtml"
    exclude-result-prefixes="d">

  <xsl:import href="/usr/share/xml/docbook/stylesheet/docbook-xsl-ns/xhtml5/docbook.xsl"/>

  <!-- Fix 1: suppress the XML declaration. omit-xml-declaration is an
       xsl:output serialization attribute, not a docbook-xsl param —
       chunker.output.omit-xml-declaration exists but only governs the
       exsl:document-based multi-file chunker (chunk.xsl/chunkfast.xsl),
       which this single-page, non-chunked build never invokes. Neither
       xhtml5/docbook.xsl nor the xhtml5/xhtml-docbook.xsl it imports
       ever sets omit-xml-declaration, so this is the only value for it
       anywhere in the merged stylesheet — no import-precedence
       tie-break is even needed. encoding="UTF-8" is carried forward
       explicitly and deliberately: the corpus has real non-ASCII
       content and upstream's own UTF-8 output is load-bearing (see
       GC-4) — this attribute must never be dropped from this
       override. -->
  <xsl:output method="xml" encoding="UTF-8" omit-xml-declaration="yes"/>

</xsl:stylesheet>
