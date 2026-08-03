package io.github.metavacua.pipeline;

import org.w3c.dom.Document;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import java.io.StringWriter;

public final class Xml {
    /** XXE-hardened, fail-fast: no DTDs, no entity expansion, no XInclude. */
    public static DocumentBuilder hardenedBuilder() {
        try {
            var f = DocumentBuilderFactory.newInstance();
            f.setNamespaceAware(true);
            f.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            f.setXIncludeAware(false);
            f.setExpandEntityReferences(false);
            return f.newDocumentBuilder();
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    /** For parsing OUR OWN renderer's output, whose first line is legitimately
     *  <!DOCTYPE html> (polyglot XHTML5): doctype tolerated, but every external
     *  fetch/expansion vector is explicitly dead (OWASP XXE guidance). Input
     *  documents keep the stricter hardenedBuilder (no doctype at all). */
    public static DocumentBuilder outputBuilder() {
        try {
            var f = DocumentBuilderFactory.newInstance();
            f.setNamespaceAware(true);
            f.setFeature("http://xml.org/sax/features/external-general-entities", false);
            f.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            f.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
            f.setXIncludeAware(false);
            f.setExpandEntityReferences(false);
            return f.newDocumentBuilder();
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    /** Identity serialization only — never an XSLT transform. On this classpath JAXP resolves
     *  to Saxon's IdentityTransformer (one engine everywhere). */
    public static String serialize(Document d) {
        try {
            var tf = TransformerFactory.newInstance();
            tf.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, "");
            tf.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");
            var t = tf.newTransformer();
            t.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "yes");
            var w = new StringWriter();
            t.transform(new DOMSource(d), new StreamResult(w));
            return w.toString();
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private Xml() {}
}
