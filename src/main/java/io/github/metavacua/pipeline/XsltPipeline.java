package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.*;
import org.w3c.dom.Document;
import javax.xml.transform.dom.DOMSource;
import java.nio.file.Path;
import java.util.Map;

public final class XsltPipeline {
    /** One Saxon processor for the whole JVM — the single XSLT engine. */
    public static final Processor SAXON = new Processor(false);

    public static XsltExecutable compile(Path xsl) {
        try {
            return SAXON.newXsltCompiler().compile(new javax.xml.transform.stream.StreamSource(xsl.toFile()));
        } catch (SaxonApiException e) { throw new IllegalStateException(e); }
    }
    public static Document apply(XsltExecutable xsl, Document in, Map<QName, String> params) {
        // Runtime-verified against Saxon 12.7 (s9api): for xsl:message terminate="yes",
        // SaxonApiException.getMessage() is the generic "Processing terminated by
        // xsl:message at line N in <stylesheet>" — it does NOT carry the xsl:message
        // text itself, despite that being the natural reading of s9api's contract. The
        // actual text ("Unmapped XHTML element: kbd", etc.) is only ever delivered via
        // the message-handler callback, so it must be captured there and attached below.
        var terminateText = new java.util.concurrent.atomic.AtomicReference<String>();
        try {
            Xslt30Transformer t = xsl.load30();
            var m = new java.util.HashMap<QName, XdmValue>();
            params.forEach((k, v) -> m.put(k, new XdmAtomicValue(v)));
            t.setStylesheetParameters(m);
            t.setMessageHandler(msg -> {
                if (msg.isTerminate()) terminateText.set(msg.getStringValue());
            });
            Document outDoc = Xml.hardenedBuilder().newDocument();
            t.applyTemplates(SAXON.newDocumentBuilder().build(new DOMSource(in)),
                             new DOMDestination(outDoc));
            return outDoc;
        } catch (SaxonApiException e) {
            String msg = terminateText.get() != null ? terminateText.get() : e.getMessage();
            throw new IllegalStateException(msg, e);
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private XsltPipeline() {}
}
