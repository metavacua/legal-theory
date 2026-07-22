<?xml version="1.0" encoding="UTF-8"?>
<!--
  html5.xsl — DocBook 5.2 → HTML5 transform
  Language Models Are Databases (llm-database-theory)
  Renders Dublin Core meta tags and Schema.org JSON-LD from 00-metadata.xml.
  Applies CSS colour-coding for finding sections:
    confirmed            → green border
    confirmed-with-caveats → blue border
    split                → amber border
-->
<xsl:stylesheet
    version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:db="http://docbook.org/ns/docbook"
    xmlns:dc="http://purl.org/dc/terms/"
    xmlns:xi="http://www.w3.org/2001/XInclude"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    exclude-result-prefixes="db dc xi xlink">

  <xsl:output method="html" version="5.0" encoding="UTF-8" indent="yes"
              doctype-system="about:legacy-compat"/>

  <!-- ============================================================
       ROOT
       ============================================================ -->
  <xsl:template match="/db:article">
    <html lang="en">
      <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title><xsl:value-of select="db:info/dc:title"/></title>

        <!-- Dublin Core meta tags -->
        <meta name="DC.title"       content="{db:info/dc:title}"/>
        <meta name="DC.creator"     content="{db:info/dc:creator}"/>
        <meta name="DC.subject"     content="{db:info/dc:subject}"/>
        <meta name="DC.description" content="{db:info/dc:description}"/>
        <meta name="DC.date"        content="{db:info/dc:date}"/>
        <meta name="DC.type"        content="{db:info/dc:type}"/>
        <meta name="DC.language"    content="{db:info/dc:language}"/>
        <meta name="DC.rights"      content="{db:info/dc:rights}"/>

        <!-- Schema.org JSON-LD (extracted from bibliomisc element) -->
        <xsl:if test="db:info/db:bibliomisc[@role='schema-org-jsonld']">
          <script type="application/ld+json">
            <xsl:value-of select="db:info/db:bibliomisc[@role='schema-org-jsonld']"/>
          </script>
        </xsl:if>

        <style>
          :root {
            --ink: #101922;
            --ink-soft: #3f4f5c;
            --rule: #d3dbe3;
            --surface: #fbfcfd;
            --amber: #cf7d18;
            --teal: #0b6169;
            --green: #1a7a4a;
            --blue: #0b3d91;
            --paper: #f5f7f9;
          }
          body { font-family: 'Georgia', serif; max-width: 820px; margin: 0 auto;
                 padding: 2rem 1.5rem; background: var(--paper); color: var(--ink);
                 font-size: 18px; line-height: 1.65; }
          h1, h2, h3, h4 { font-family: system-ui, sans-serif; }
          h1 { font-size: 2.2rem; margin-bottom: 0.25em; }
          h2 { font-size: 1.55rem; border-bottom: 1px solid var(--rule); padding-bottom: 0.3em; }
          h3 { font-size: 1.2rem; }
          h4 { font-size: 1rem; text-transform: uppercase; letter-spacing: 0.08em;
               color: var(--ink-soft); }
          pre, code { font-family: 'JetBrains Mono', monospace; font-size: 0.85em; }
          pre { background: #0b1418; color: #c9d6d3; padding: 1.1rem 1.3rem;
                border-radius: 6px; overflow-x: auto; }
          blockquote { border-left: 3px solid var(--teal); margin: 1.5rem 0;
                       padding: 0.3rem 0 0.3rem 1.2rem; color: var(--ink-soft); }
          table { border-collapse: collapse; width: 100%; margin: 1.5rem 0; font-size: 0.9rem; }
          th, td { border: 1px solid var(--rule); padding: 0.5rem 0.8rem; text-align: left; }
          th { background: var(--surface); font-family: system-ui, sans-serif; }
          a { color: var(--teal); }

          /* Finding sections */
          section[data-condition="confirmed"] {
            border-left: 4px solid var(--green);
            padding-left: 1.2rem;
            margin-left: -1.2rem;
          }
          section[data-condition="confirmed-with-caveats"] {
            border-left: 4px solid var(--blue);
            padding-left: 1.2rem;
            margin-left: -1.2rem;
          }
          section[data-condition="split"] {
            border-left: 4px solid var(--amber);
            padding-left: 1.2rem;
            margin-left: -1.2rem;
          }

          nav.site-nav { font-family: system-ui, sans-serif; font-size: 0.85rem;
                         margin-bottom: 1.5rem; }
          nav.site-nav a { text-decoration: none; }
          nav.site-nav a:hover { text-decoration: underline; }

          header.doc-header { margin-bottom: 2.5rem; }
          .abstract { background: var(--surface); border: 1px solid var(--rule);
                      border-radius: 6px; padding: 1.2rem 1.5rem; margin: 1.5rem 0; }
          .abstract p:first-child::before { content: "Abstract. "; font-weight: bold; }
          footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--rule);
                   font-size: 0.8rem; color: var(--ink-soft); }
        </style>
      </head>
      <body>
        <nav class="site-nav">
          <a href="/legal-theory/">legal-theory</a>
          <xsl:text> · </xsl:text>
          <a href="/legal-theory/index.html">Index</a>
        </nav>
        <xsl:apply-templates/>
        <footer>
          <p>
            <xsl:value-of select="db:info/db:legalnotice/db:para"/>
          </p>
        </footer>
      </body>
    </html>
  </xsl:template>

  <!-- ============================================================
       INFO BLOCK → document header
       ============================================================ -->
  <xsl:template match="db:info">
    <header class="doc-header">
      <h1><xsl:value-of select="dc:title"/></h1>
      <p class="byline">
        By <xsl:value-of select="db:authorgroup/db:author/db:personname/db:firstname"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="db:authorgroup/db:author/db:personname/db:othername"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="db:authorgroup/db:author/db:personname/db:surname"/>
        <xsl:text> — </xsl:text>
        <xsl:value-of select="dc:date"/>
      </p>
      <xsl:apply-templates select="db:abstract"/>
    </header>
  </xsl:template>

  <xsl:template match="db:abstract">
    <div class="abstract">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- suppress legalnotice from body (rendered in footer) -->
  <xsl:template match="db:legalnotice | db:bibliomisc"/>

  <!-- ============================================================
       STRUCTURAL ELEMENTS
       ============================================================ -->
  <xsl:template match="db:section">
    <section>
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@condition">
        <xsl:attribute name="data-condition"><xsl:value-of select="@condition"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </section>
  </xsl:template>

  <xsl:template match="db:section/db:title">
    <xsl:variable name="depth" select="count(ancestor::db:section)"/>
    <xsl:choose>
      <xsl:when test="$depth = 1"><h2><xsl:apply-templates/></h2></xsl:when>
      <xsl:when test="$depth = 2"><h3><xsl:apply-templates/></h3></xsl:when>
      <xsl:otherwise><h4><xsl:apply-templates/></h4></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="db:article/db:title | db:article/db:subtitle"/>

  <xsl:template match="db:para">
    <p><xsl:apply-templates/></p>
  </xsl:template>

  <xsl:template match="db:blockquote">
    <blockquote>
      <xsl:apply-templates select="db:para"/>
      <xsl:if test="db:attribution">
        <cite>— <xsl:value-of select="db:attribution"/></cite>
      </xsl:if>
    </blockquote>
  </xsl:template>

  <xsl:template match="db:attribution"/>

  <xsl:template match="db:programlisting">
    <pre><code><xsl:apply-templates/></code></pre>
  </xsl:template>

  <!-- db:literallayout: defense-in-depth (see docs/scripts/convert_to_docbook.py's
       _strip_trailing_whitespace) — the conversion tool strips trailing
       whitespace before pandoc runs, so pandoc should never emit this for an
       accidental Markdown hard break anymore, but if a document ever has a
       genuinely-intentional preformatted block (an address, a line-block/verse),
       render its line breaks correctly instead of falling through to unstyled
       bare text with no wrapping element. -->
  <xsl:template match="db:screen | db:literallayout">
    <pre><xsl:apply-templates/></pre>
  </xsl:template>

  <xsl:template match="db:itemizedlist">
    <ul><xsl:apply-templates/></ul>
  </xsl:template>

  <xsl:template match="db:orderedlist">
    <ol><xsl:apply-templates/></ol>
  </xsl:template>

  <xsl:template match="db:listitem">
    <li><xsl:apply-templates/></li>
  </xsl:template>

  <xsl:template match="db:emphasis[@role='bold']">
    <strong><xsl:apply-templates/></strong>
  </xsl:template>

  <xsl:template match="db:emphasis[@role='italic'] | db:emphasis">
    <em><xsl:apply-templates/></em>
  </xsl:template>

  <xsl:template match="db:command | db:code">
    <code><xsl:apply-templates/></code>
  </xsl:template>

  <xsl:template match="db:quote">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="db:citation">
    <cite>[<xsl:apply-templates/>]</cite>
  </xsl:template>

  <xsl:template match="db:link[@xlink:href]">
    <a href="{@xlink:href}"><xsl:apply-templates/></a>
  </xsl:template>

  <xsl:template match="db:subscript">
    <sub><xsl:apply-templates/></sub>
  </xsl:template>

  <xsl:template match="db:mathphrase">
    <var><xsl:apply-templates/></var>
  </xsl:template>

  <!-- Tables -->
  <xsl:template match="db:table">
    <figure>
      <xsl:if test="db:title">
        <figcaption><xsl:value-of select="db:title"/></figcaption>
      </xsl:if>
      <xsl:apply-templates select="db:tgroup"/>
    </figure>
  </xsl:template>

  <xsl:template match="db:tgroup">
    <table>
      <xsl:apply-templates/>
    </table>
  </xsl:template>

  <xsl:template match="db:thead">
    <thead><xsl:apply-templates/></thead>
  </xsl:template>

  <xsl:template match="db:tbody">
    <tbody><xsl:apply-templates/></tbody>
  </xsl:template>

  <xsl:template match="db:row">
    <tr><xsl:apply-templates/></tr>
  </xsl:template>

  <xsl:template match="db:thead/db:row/db:entry">
    <th><xsl:apply-templates/></th>
  </xsl:template>

  <xsl:template match="db:tbody/db:row/db:entry">
    <td><xsl:apply-templates/></td>
  </xsl:template>

  <xsl:template match="db:colspec | db:tgroup/@cols"/>

  <!-- Pass through text -->
  <xsl:template match="text()">
    <xsl:value-of select="."/>
  </xsl:template>

</xsl:stylesheet>
