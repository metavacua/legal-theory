<?xml version="1.0" encoding="UTF-8"?>
<!--
  Workaround for xslTNG 2.8.3 upstream gap: chunk-cleanup's lang inheritance
  (modules/chunk-cleanup.xsl:218) only consults ancestors, so a standalone
  chunk-root article's authored xml:lang never reaches html. Lifts the
  AUTHORED value only, no default, no fabrication. Remove when upstream
  propagates chunk-root lang.
-->
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:h="http://www.w3.org/1999/xhtml"
    exclude-result-prefixes="xsl h">

  <!-- Mirrors main.xsl's own <xsl:output> so this second-pass transform
       serializes byte-identically to xslTNG's own output (HTML5 doctype,
       no XML declaration, unindented). -->
  <xsl:output method="xhtml" encoding="utf-8" indent="no" html-version="5"
              omit-xml-declaration="yes"/>

  <xsl:mode on-no-match="shallow-copy"/>

  <!-- If html lacks @lang and a descendant article carries the authored
       lang, lift the FIRST such article's @lang (document order) onto html.
       No fallback/default is applied when no such article exists. -->
  <xsl:template match="h:html[not(@lang)][.//h:article[@lang]]">
    <xsl:copy>
      <xsl:attribute name="lang" select="(.//h:article[@lang])[1]/@lang"/>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
