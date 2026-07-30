<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt">
  <title>DCTERMS completeness policy for this project's DocBook articles</title>

  <!-- DocBook's own grammar (validated separately, via the real OASIS
       DocBook 5.2 RELAX NG schema and jing, see convert_to_docbook.py's
       validate()) correctly has no opinion about which <info> fields a
       document must carry, or what dc:type must say. Those are this
       project's own policy, expressed here as a real ISO/IEC 19757-3
       Schematron schema instead of a hand-rolled Python tree-walk. -->

  <ns prefix="db" uri="http://docbook.org/ns/docbook"/>
  <ns prefix="dc" uri="http://purl.org/dc/terms/"/>

  <pattern id="dcterms-completeness">
    <rule context="db:article">
      <assert test="db:info">missing info</assert>
    </rule>
    <rule context="db:article/db:info">
      <assert test="db:title">missing title</assert>
      <assert test="db:pubdate">missing pubdate</assert>
      <assert test="db:biblioid">missing biblioid</assert>
      <!-- Two asserts, not one, so the diagnostic can distinguish
           "dc:type absent or empty" (found None) from "dc:type present
           with the wrong value" (found '<value>'): Schematron/XPath 1.0
           has no if/then/else expression to pick between the two
           messages inline, and the two tests are mutually exclusive by
           construction (exactly one can ever fail for a given
           document), so together they behave as one two-way check. -->
      <assert test="dc:type/text()">dc:type must be exactly "Text", found None</assert>
      <assert test="not(dc:type/text()) or dc:type = 'Text'">dc:type must be exactly "Text", found '<value-of select="dc:type"/>'</assert>
    </rule>
  </pattern>
</schema>
