"""Convert a Markdown document to validated, XSLT-buildable DocBook 5.2 XML."""

import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

DB_NS = "http://docbook.org/ns/docbook"
XI_NS = "http://www.w3.org/2001/XInclude"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", DB_NS)
ET.register_namespace("xi", XI_NS)
ET.register_namespace("xlink", XLINK_NS)


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    if not text:
        return "s"
    if re.match(r"^[0-9]", text):
        text = f"s-{text}"
    return text


def extract_title(md_path):
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^#{1,6}\s+(.*)", line)
            if m:
                return re.sub(r"[*_]", "", m.group(1)).strip()
    return Path(md_path).stem.replace("-", " ").replace("_", " ").title()


def pandoc_to_docbook_fragment(md_path):
    result = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "docbook5", str(md_path)],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def wrap_fragment(fragment, xml_id, title, metadata_href):
    # Pandoc emits one or more top-level <section> elements with no
    # shared root, each carrying its own repeated xmlns declarations.
    # Strip the repeats and wrap everything in one parseable <root>.
    stripped = fragment.replace(f'xmlns="{DB_NS}" ', "").replace(
        f'xmlns:xlink="{XLINK_NS}" ', ""
    )
    wrapped = f'<root xmlns="{DB_NS}" xmlns:xlink="{XLINK_NS}">{stripped}</root>'
    root = ET.fromstring(wrapped)
    children = list(root)

    article = ET.Element(f"{{{DB_NS}}}article")
    article.set("version", "5.2")
    article.set(f"{{{XML_NS}}}id", xml_id)
    article.set(f"{{{XML_NS}}}lang", "en")

    xi_include = ET.SubElement(article, f"{{{XI_NS}}}include")
    xi_include.set("href", metadata_href)

    title_el = ET.SubElement(article, f"{{{DB_NS}}}title")
    title_el.text = title

    # A single top-level <section> whose own <title> just duplicates
    # the article title we already set: unwrap it so its children
    # become the article's direct children, matching the flatter
    # structure the hand-authored paper already uses. Multiple
    # top-level siblings have no single title to unwrap from, so they
    # stay as direct article children as-is.
    unwrapped = len(children) == 1 and children[0].tag == f"{{{DB_NS}}}section"
    if unwrapped:
        for child in list(children[0]):
            if child.tag != f"{{{DB_NS}}}title":
                article.append(child)
    else:
        for child in children:
            article.append(child)

    sanitize_xml_ids(article)
    return article, unwrapped


def sanitize_xml_ids(article):
    xml_id_attr = f"{{{XML_NS}}}id"
    for el in article.iter():
        value = el.get(xml_id_attr)
        if value and re.match(r"^[0-9]", value):
            el.set(xml_id_attr, f"s-{value}")


def write_metadata(meta_path, title):
    escaped_title = xml_escape(title)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/">
  <dc:title>{escaped_title}</dc:title>
  <dc:creator>Ian D.L.N. McLean</dc:creator>
  <dc:publisher>metavacua/legal-theory (GitHub)</dc:publisher>
  <dc:type>Article</dc:type>
  <dc:language>en</dc:language>
  <dc:rights>CC BY-SA 4.0</dc:rights>
  <authorgroup>
    <author>
      <personname>
        <firstname>Ian</firstname>
        <othername role="middle">D.L.N.</othername>
        <surname>McLean</surname>
      </personname>
      <email>metavacua@gmail.com</email>
    </author>
  </authorgroup>
  <legalnotice>
    <para>Copyright &#169; 2026 Ian D.L.N. McLean. Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). This document publishes general legal analysis and does not constitute legal advice.</para>
  </legalnotice>
</info>
"""
    Path(meta_path).write_text(content, encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "docs" / "schema" / "docbook-corpus.rnc"
HTML5_XSL_PATH = REPO_ROOT / "docs" / "xsl" / "html5.xsl"


def validate(xml_path):
    errors = []
    wf = subprocess.run(
        ["xmllint", "--noout", "--xinclude", str(xml_path)],
        capture_output=True, text=True,
    )
    if wf.returncode != 0:
        errors.append(wf.stderr.strip())
        return errors  # schema validation is meaningless on malformed XML

    rng = subprocess.run(
        ["jing", "-c", str(SCHEMA_PATH), str(xml_path)],
        capture_output=True, text=True,
    )
    if rng.returncode != 0:
        errors.append(rng.stdout.strip() or rng.stderr.strip())
    return errors


def build_html(xml_path, out_path):
    result = subprocess.run(
        ["xsltproc", "--xinclude", str(HTML5_XSL_PATH), str(xml_path)],
        capture_output=True, text=True, check=True,
    )
    Path(out_path).write_text(result.stdout, encoding="utf-8")
