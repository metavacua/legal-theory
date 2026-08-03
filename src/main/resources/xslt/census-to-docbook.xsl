<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://docbook.org/ns/docbook" exclude-result-prefixes="#all">
  <xsl:output method="xml"/>
  <xsl:template match="/census">
    <para>Generated <xsl:value-of select="@generated"/>. Documents:
      <xsl:value-of select="@total"/>; published: <xsl:value-of select="@published"/>.</para>
    <informaltable>
      <thead><tr><th>Document</th><th>Published</th><th>Title class</th>
        <th>Bibliography region</th><th>First failing gate</th></tr></thead>
      <tbody>
        <xsl:for-each select="doc">
          <tr>
            <td><xsl:value-of select="@path"/></td>
            <td><xsl:value-of select="@published"/></td>
            <td><xsl:value-of select="@titleClass"/></td>
            <td><xsl:value-of select="if (check[@id='biblio-region']/@present eq 'true')
                 then 'yes (' || check[@id='biblio-region']/@count || ')' else 'no'"/></td>
            <td><xsl:value-of select="(gate[@status='fail'])[1]/(@id || ': ' || message)"/></td>
          </tr>
        </xsl:for-each>
      </tbody>
    </informaltable>
  </xsl:template>
</xsl:stylesheet>
