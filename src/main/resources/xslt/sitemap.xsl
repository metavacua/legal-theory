<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" exclude-result-prefixes="#all">
  <xsl:output method="xml" indent="yes"/>
  <xsl:param name="site-base" select="'https://metavacua.github.io/legal-theory/'"/>
  <xsl:template match="/census">
    <urlset>
      <url><loc><xsl:value-of select="$site-base"/></loc></url>
      <xsl:for-each select="doc[@published='true']">
        <url><loc><xsl:value-of select="$site-base ||
          replace(replace(@path, '^docs/', ''), '\.md$', '.xhtml')"/></loc></url>
      </xsl:for-each>
    </urlset>
  </xsl:template>
</xsl:stylesheet>
