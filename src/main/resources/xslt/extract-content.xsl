<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:h="http://www.w3.org/1999/xhtml"
    xmlns:db="http://docbook.org/ns/docbook"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    exclude-result-prefixes="#all">
  <xsl:output method="text"/>
  <xsl:param name="mode" as="xs:string" required="yes" xmlns:xs="http://www.w3.org/2001/XMLSchema"/>

  <!-- CALIBRATION POINT (the one permitted adjustment, locked by the base-case
       test): furniture excluded from xslTNG-rendered XHTML. -->
  <xsl:variable name="xhtml-scope"
      select="if (//h:main) then //h:main else //h:body"/>

  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="$mode eq 'xhtml'">
        <!-- CALIBRATION (round 1, base-case run): xslTNG auto-generates a
             Table of Contents (div class="lot toc", live-verified at
             modules/toc.xsl) and per-heading section-number furniture
             (span class="label" + span class="sep", live-verified at
             modules/blocks.xsl/titlepage.xsl) that has no counterpart in
             the authored source. Both are excluded here, structurally
             the SAME kind of ancestor-exclusion predicate as nav/header/
             footer/script/style above, just naming the two furniture
             containers xslTNG actually emits. Deliberately NOT suppressed
             via the xslTNG render-time params that exist for this
             (auto-toc, section-numbers, both in param.xsl): those are
             site-wide rendering knobs; flipping them would remove the
             TOC/numbering from every published page, a product decision
             out of scope for a content-preservation comparator. Excluding
             here scopes the fix to the oracle, not the renderer.

             CALIBRATION (round 2): xslTNG wraps EVERY section's own title in
             a header (section/header/h2, live-verified), not just the
             page-level masthead the brief's original "ancestor::h:header"
             predicate meant to exclude. A blanket header exclusion silently
             dropped every section heading's text from the xhtml-mode
             comparison, a real content-preservation hole, not furniture,
             caught only because P3's heading text ("About this site") failed
             to appear at all in P2(P1)'s extraction. Narrowed to
             "ancestor::h:header[not(ancestor::h:section)]": excludes only a
             header with no enclosing section (the article-level masthead,
             which carries the front-matter title, itself out of scope per
             the controller's byte-verified-title resolution, since P3 never
             puts that title in $xhtml-scope at all), while a section's own
             header stays IN scope so its heading text is compared. -->
        <xsl:for-each select="$xhtml-scope//text()[normalize-space()]
            [not(ancestor::h:nav
                 or ancestor::h:header[not(ancestor::h:section)]
                 or ancestor::h:footer or ancestor::h:script or ancestor::h:style
                 or ancestor::h:div[contains-token(@class, 'toc')]
                 or ancestor::h:span[contains-token(@class, 'label')]
                 or ancestor::h:span[contains-token(@class, 'sep')])]">
          <xsl:value-of select="normalize-space(.)"/><xsl:text>&#10;</xsl:text>
        </xsl:for-each>
        <xsl:text>===LINKS===&#10;</xsl:text>
        <xsl:for-each select="distinct-values($xhtml-scope//h:a
            [not(ancestor::h:nav
                 or ancestor::h:header[not(ancestor::h:section)]
                 or ancestor::h:footer
                 or ancestor::h:div[contains-token(@class, 'toc')])]/@href)">
          <xsl:sort/><xsl:value-of select="."/><xsl:text>&#10;</xsl:text>
        </xsl:for-each>
      </xsl:when>
      <xsl:otherwise> <!-- docbook: title + body, excluding generated info fields -->
        <xsl:for-each select="(//db:info/db:title | //db:article/(* except db:info))
            //text()[normalize-space()] | //db:info/db:title/text()[normalize-space()]">
          <xsl:value-of select="normalize-space(.)"/><xsl:text>&#10;</xsl:text>
        </xsl:for-each>
        <xsl:text>===LINKS===&#10;</xsl:text>
        <xsl:for-each select="distinct-values(//db:link/@xlink:href)">
          <xsl:sort/><xsl:value-of select="."/><xsl:text>&#10;</xsl:text>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
