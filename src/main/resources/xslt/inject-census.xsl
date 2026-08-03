<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:db="http://docbook.org/ns/docbook" exclude-result-prefixes="#all">
  <xsl:param name="census-fragment-uri" as="xs:string" required="yes"
             xmlns:xs="http://www.w3.org/2001/XMLSchema"/>
  <xsl:mode on-no-match="shallow-copy"/>
  <xsl:template match="db:section[@xml:id='census']/db:para">
    <!-- doc(...)/* is the no-namespace <census-fragment> carrier (census-to-docbook.xsl);
         copy its children (para, informaltable), never the carrier itself. -->
    <xsl:copy-of select="doc($census-fragment-uri)/*/node()"/>
  </xsl:template>
</xsl:stylesheet>
