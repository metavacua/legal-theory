<?xml version="1.0" encoding="UTF-8"?>
<!--
  latex.xsl — DocBook 5.2 → LaTeX (article class) transform
  Language Models Are Databases (llm-database-theory)
  Produces a pdflatex-compilable .tex file.
-->
<xsl:stylesheet
    version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:db="http://docbook.org/ns/docbook"
    xmlns:dc="http://purl.org/dc/terms/"
    exclude-result-prefixes="db dc">

  <xsl:output method="text" encoding="UTF-8"/>

  <!-- ============================================================
       ROOT
       ============================================================ -->
  <xsl:template match="/db:article">
    <xsl:text>\documentclass[12pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{geometry}
\geometry{margin=2.5cm}

\lstset{
  basicstyle=\ttfamily\small,
  backgroundcolor=\color{black!5},
  frame=single,
  breaklines=true,
  breakatwhitespace=true,
  columns=fixed
}

\hypersetup{
  colorlinks=true,
  linkcolor=teal,
  urlcolor=teal,
  citecolor=teal
}

</xsl:text>
    <!-- Title block from metadata -->
    <xsl:text>\title{</xsl:text>
    <xsl:call-template name="latex-escape">
      <xsl:with-param name="text" select="db:info/dc:title"/>
    </xsl:call-template>
    <xsl:text>}
\author{</xsl:text>
    <xsl:value-of select="db:info/db:authorgroup/db:author/db:personname/db:firstname"/>
    <xsl:text> </xsl:text>
    <xsl:value-of select="db:info/db:authorgroup/db:author/db:personname/db:othername"/>
    <xsl:text> </xsl:text>
    <xsl:value-of select="db:info/db:authorgroup/db:author/db:personname/db:surname"/>
    <xsl:text>}
\date{</xsl:text>
    <xsl:value-of select="db:info/dc:date"/>
    <xsl:text>}

\begin{document}
\maketitle

</xsl:text>
    <!-- Abstract -->
    <xsl:if test="db:info/db:abstract">
      <xsl:text>\begin{abstract}
</xsl:text>
      <xsl:apply-templates select="db:info/db:abstract/db:para"/>
      <xsl:text>\end{abstract}

</xsl:text>
    </xsl:if>

    <xsl:apply-templates select="db:section"/>

    <xsl:text>
\end{document}
</xsl:text>
  </xsl:template>

  <!-- suppress info in body (already used for \title etc.) -->
  <xsl:template match="db:info"/>

  <!-- ============================================================
       SECTIONS
       ============================================================ -->
  <xsl:template match="db:section">
    <xsl:variable name="depth" select="count(ancestor::db:section)"/>
    <xsl:choose>
      <xsl:when test="$depth = 0">
        <xsl:text>\section{</xsl:text>
        <xsl:call-template name="latex-escape">
          <xsl:with-param name="text" select="db:title"/>
        </xsl:call-template>
        <xsl:text>}
\label{</xsl:text><xsl:value-of select="@xml:id"/><xsl:text>}

</xsl:text>
      </xsl:when>
      <xsl:when test="$depth = 1">
        <xsl:text>\subsection{</xsl:text>
        <xsl:call-template name="latex-escape">
          <xsl:with-param name="text" select="db:title"/>
        </xsl:call-template>
        <xsl:text>}

</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>\subsubsection{</xsl:text>
        <xsl:call-template name="latex-escape">
          <xsl:with-param name="text" select="db:title"/>
        </xsl:call-template>
        <xsl:text>}

</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:apply-templates select="*[not(self::db:title)]"/>
  </xsl:template>

  <!-- ============================================================
       PARAGRAPHS AND INLINE
       ============================================================ -->
  <xsl:template match="db:para">
    <xsl:apply-templates/>
    <xsl:text>

</xsl:text>
  </xsl:template>

  <xsl:template match="db:emphasis[@role='bold']">
    <xsl:text>\textbf{</xsl:text><xsl:apply-templates/><xsl:text>}</xsl:text>
  </xsl:template>

  <xsl:template match="db:emphasis[@role='italic'] | db:emphasis">
    <xsl:text>\textit{</xsl:text><xsl:apply-templates/><xsl:text>}</xsl:text>
  </xsl:template>

  <xsl:template match="db:command | db:code">
    <xsl:text>\texttt{</xsl:text><xsl:apply-templates/><xsl:text>}</xsl:text>
  </xsl:template>

  <xsl:template match="db:quote">
    <xsl:text>``</xsl:text><xsl:apply-templates/><xsl:text>''</xsl:text>
  </xsl:template>

  <xsl:template match="db:citation">
    <xsl:text>~\cite{</xsl:text><xsl:apply-templates/><xsl:text>}</xsl:text>
  </xsl:template>

  <xsl:template match="db:subscript">
    <xsl:text>$_{</xsl:text><xsl:apply-templates/><xsl:text>}$</xsl:text>
  </xsl:template>

  <xsl:template match="db:mathphrase">
    <xsl:text>$</xsl:text><xsl:apply-templates/><xsl:text>$</xsl:text>
  </xsl:template>

  <xsl:template match="db:link[@xlink:href]"
                xmlns:xlink="http://www.w3.org/1999/xlink">
    <xsl:text>\href{</xsl:text>
    <xsl:value-of select="@xlink:href"/>
    <xsl:text>}{</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>}</xsl:text>
  </xsl:template>

  <!-- ============================================================
       BLOCK ELEMENTS
       ============================================================ -->
  <xsl:template match="db:blockquote">
    <xsl:text>\begin{quote}
</xsl:text>
    <xsl:apply-templates select="db:para"/>
    <xsl:if test="db:attribution">
      <xsl:text>--- \textit{</xsl:text>
      <xsl:value-of select="db:attribution"/>
      <xsl:text>}
</xsl:text>
    </xsl:if>
    <xsl:text>\end{quote}

</xsl:text>
  </xsl:template>

  <xsl:template match="db:attribution"/>

  <xsl:template match="db:programlisting | db:screen">
    <xsl:text>\begin{lstlisting}
</xsl:text>
    <xsl:value-of select="."/>
    <xsl:text>
\end{lstlisting}

</xsl:text>
  </xsl:template>

  <xsl:template match="db:itemizedlist">
    <xsl:text>\begin{itemize}
</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>\end{itemize}

</xsl:text>
  </xsl:template>

  <xsl:template match="db:orderedlist">
    <xsl:text>\begin{enumerate}
</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>\end{enumerate}

</xsl:text>
  </xsl:template>

  <xsl:template match="db:listitem">
    <xsl:text>  \item </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Tables -->
  <xsl:template match="db:table">
    <xsl:text>\begin{table}[htbp]
\centering
</xsl:text>
    <xsl:if test="db:title">
      <xsl:text>\caption{</xsl:text>
      <xsl:call-template name="latex-escape">
        <xsl:with-param name="text" select="db:title"/>
      </xsl:call-template>
      <xsl:text>}
</xsl:text>
    </xsl:if>
    <xsl:apply-templates select="db:tgroup"/>
    <xsl:text>\end{table}

</xsl:text>
  </xsl:template>

  <xsl:template match="db:tgroup">
    <xsl:variable name="cols" select="@cols"/>
    <xsl:text>\begin{tabular}{</xsl:text>
    <xsl:call-template name="col-spec">
      <xsl:with-param name="n" select="$cols"/>
    </xsl:call-template>
    <xsl:text>}
\toprule
</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>\bottomrule
\end{tabular}
</xsl:text>
  </xsl:template>

  <xsl:template name="col-spec">
    <xsl:param name="n"/>
    <xsl:if test="$n > 0">
      <xsl:text>p{</xsl:text>
      <xsl:value-of select="format-number(0.9 div $n, '0.00')"/>
      <xsl:text>\textwidth}</xsl:text>
      <xsl:if test="$n > 1"><xsl:text> </xsl:text></xsl:if>
      <xsl:call-template name="col-spec">
        <xsl:with-param name="n" select="$n - 1"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

  <xsl:template match="db:thead">
    <xsl:apply-templates/>
    <xsl:text>\midrule
</xsl:text>
  </xsl:template>

  <xsl:template match="db:tbody">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="db:row">
    <xsl:for-each select="db:entry">
      <xsl:if test="position() > 1"><xsl:text> &amp; </xsl:text></xsl:if>
      <xsl:apply-templates/>
    </xsl:for-each>
    <xsl:text> \\
</xsl:text>
  </xsl:template>

  <xsl:template match="db:entry"/>
  <xsl:template match="db:colspec"/>

  <!-- ============================================================
       TEXT + LATEX-ESCAPE HELPER
       ============================================================ -->
  <xsl:template match="text()">
    <xsl:call-template name="latex-escape">
      <xsl:with-param name="text" select="."/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="latex-escape">
    <xsl:param name="text"/>
    <!-- Minimal escaping for the most common special characters -->
    <xsl:variable name="s1">
      <xsl:call-template name="str-replace">
        <xsl:with-param name="text" select="$text"/>
        <xsl:with-param name="find" select="'&amp;'"/>
        <xsl:with-param name="replace" select="'\&amp;'"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="s2">
      <xsl:call-template name="str-replace">
        <xsl:with-param name="text" select="$s1"/>
        <xsl:with-param name="find" select="'%'"/>
        <xsl:with-param name="replace" select="'\%'"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="s3">
      <xsl:call-template name="str-replace">
        <xsl:with-param name="text" select="$s2"/>
        <xsl:with-param name="find" select="'_'"/>
        <xsl:with-param name="replace" select="'\_'"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:value-of select="$s3"/>
  </xsl:template>

  <xsl:template name="str-replace">
    <xsl:param name="text"/>
    <xsl:param name="find"/>
    <xsl:param name="replace"/>
    <xsl:choose>
      <xsl:when test="contains($text, $find)">
        <xsl:value-of select="substring-before($text, $find)"/>
        <xsl:value-of select="$replace"/>
        <xsl:call-template name="str-replace">
          <xsl:with-param name="text" select="substring-after($text, $find)"/>
          <xsl:with-param name="find" select="$find"/>
          <xsl:with-param name="replace" select="$replace"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise><xsl:value-of select="$text"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
