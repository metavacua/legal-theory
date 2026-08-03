<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt3">
  <sch:ns prefix="db" uri="http://docbook.org/ns/docbook"/>
  <sch:ns prefix="dc" uri="http://purl.org/dc/terms/"/>
  <sch:pattern>
    <sch:rule context="db:article/db:info">
      <!-- W3C ACT rule 2779a5: page must have a non-empty title. Enforced here
           because the pinned XHTML5 RELAX NG grammar accepts an empty title. -->
      <sch:assert test="normalize-space(db:title) ne ''"
        >info/title must be non-empty (authored via front matter or native DocBook; never generated)</sch:assert>
      <sch:assert test="db:pubdate castable as xs:date"
        >info/pubdate must be a valid ISO date</sch:assert>
      <sch:assert test="starts-with(db:biblioid[@class='uri'], 'https://github.com/metavacua/legal-theory/blob/main/')"
        >info/biblioid[@class='uri'] must carry the canonical identity prefix</sch:assert>
      <sch:assert test="dc:type eq 'Text'"
        >dc:type must be the DCMI Type Vocabulary literal 'Text'</sch:assert>
    </sch:rule>
  </sch:pattern>
</sch:schema>
