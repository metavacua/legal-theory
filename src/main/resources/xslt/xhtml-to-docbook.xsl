<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:h="http://www.w3.org/1999/xhtml"
    xmlns="http://docbook.org/ns/docbook"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:dc="http://purl.org/dc/terms/"
    xmlns:f="urn:legal-theory:f"
    exclude-result-prefixes="xsl xs h f">

  <xsl:output method="xml" indent="yes"/>
  <xsl:param name="authored-title" as="xs:string" select="''"/>
  <xsl:param name="source-path" as="xs:string" required="yes"/>
  <xsl:param name="manifest-uri" as="xs:string" required="yes"/>

  <xsl:variable name="mdoc" select="doc($manifest-uri)/manifest/doc[@path eq $source-path]"/>

  <xsl:template match="/h:html">
    <xsl:if test="empty($mdoc)">
      <xsl:message terminate="yes" select="'No manifest entry for ' || $source-path"/>
    </xsl:if>
    <article version="5.2">
      <info>
        <title><xsl:value-of select="$authored-title"/></title>
        <pubdate role="generated-from-git-first-commit"><xsl:value-of select="$mdoc/@pubdate"/></pubdate>
        <biblioid class="uri" role="generated-from-path"><xsl:value-of select="$mdoc/@biblioid"/></biblioid>
        <dc:type>Text</dc:type>
      </info>
      <xsl:sequence select="f:sectionize(h:body/node(), 1)"/>
    </article>
  </xsl:template>

  <!-- Flat h1..h6 siblings -> nested sections. A level with no headings recurses
       deeper, so an h1->h3 skip nests the h3 section directly (gap closed). -->
  <xsl:function name="f:sectionize" as="node()*">
    <xsl:param name="nodes" as="node()*"/>
    <xsl:param name="level" as="xs:integer"/>
    <xsl:choose>
      <xsl:when test="$level gt 6"><xsl:apply-templates select="$nodes"/></xsl:when>
      <xsl:otherwise>
        <xsl:for-each-group select="$nodes"
            group-starting-with="h:*[local-name() eq 'h' || string($level)]">
          <xsl:choose>
            <xsl:when test="self::h:*[local-name() eq 'h' || string($level)]">
              <section>
                <title><xsl:apply-templates/></title>
                <xsl:sequence select="f:sectionize(tail(current-group()), $level + 1)"/>
              </section>
            </xsl:when>
            <xsl:otherwise>
              <xsl:sequence select="f:sectionize(current-group(), $level + 1)"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:for-each-group>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:function>

  <!-- ============ fixed element mappings (one rule per element) ============ -->
  <xsl:template match="h:p"><para><xsl:apply-templates/></para></xsl:template>
  <xsl:template match="h:ul"><itemizedlist><xsl:apply-templates/></itemizedlist></xsl:template>
  <xsl:template match="h:ol"><orderedlist><xsl:apply-templates/></orderedlist></xsl:template>
  <xsl:template match="h:li">
    <listitem>
      <xsl:for-each-group select="node()" group-adjacent="boolean(
          self::h:p or self::h:ul or self::h:ol or self::h:pre
          or self::h:blockquote or self::h:table)">
        <xsl:choose>
          <xsl:when test="current-grouping-key()"><xsl:apply-templates select="current-group()"/></xsl:when>
          <xsl:when test="not(normalize-space(string-join(current-group() ! string(.), '')))"/>
          <xsl:otherwise><para><xsl:apply-templates select="current-group()"/></para></xsl:otherwise>
        </xsl:choose>
      </xsl:for-each-group>
    </listitem>
  </xsl:template>
  <xsl:template match="h:em"><emphasis><xsl:apply-templates/></emphasis></xsl:template>
  <xsl:template match="h:strong"><emphasis role="strong"><xsl:apply-templates/></emphasis></xsl:template>
  <xsl:template match="h:a[@href]"><link xlink:href="{@href}"><xsl:apply-templates/></link></xsl:template>
  <xsl:template match="h:code[parent::h:pre]"><xsl:apply-templates/></xsl:template>
  <xsl:template match="h:pre"><programlisting><xsl:value-of select="."/></programlisting></xsl:template>
  <xsl:template match="h:code"><code><xsl:apply-templates/></code></xsl:template>
  <xsl:template match="h:blockquote"><blockquote><xsl:apply-templates/></blockquote></xsl:template>
  <xsl:template match="h:img">
    <inlinemediaobject><imageobject><imagedata fileref="{@src}"/></imageobject></inlinemediaobject>
  </xsl:template>
  <xsl:template match="h:table"><informaltable><xsl:apply-templates/></informaltable></xsl:template>
  <xsl:template match="h:thead"><thead><xsl:apply-templates/></thead></xsl:template>
  <xsl:template match="h:tbody"><tbody><xsl:apply-templates/></tbody></xsl:template>
  <xsl:template match="h:tr"><tr><xsl:apply-templates/></tr></xsl:template>
  <xsl:template match="h:th"><th><xsl:apply-templates/></th></xsl:template>
  <xsl:template match="h:td"><td><xsl:apply-templates/></td></xsl:template>

  <!-- The two specified drops (presentational, no DocBook equivalent). -->
  <xsl:template match="h:hr | h:br"/>
  <!-- head/title handled at info level; never body content. -->
  <xsl:template match="h:head"/>

  <!-- Total-function enforcement: anything unmapped is a hard failure. -->
  <xsl:template match="h:*">
    <xsl:message terminate="yes" select="'Unmapped XHTML element: ' || local-name()"/>
  </xsl:template>
  <xsl:template match="text()"><xsl:value-of select="."/></xsl:template>
</xsl:stylesheet>
