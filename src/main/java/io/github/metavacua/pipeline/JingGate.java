package io.github.metavacua.pipeline;

import com.thaiopensource.util.PropertyMapBuilder;
import com.thaiopensource.validate.ValidateProperty;
import com.thaiopensource.validate.ValidationDriver;
import com.thaiopensource.validate.rng.CompactSchemaReader;
import org.xml.sax.ErrorHandler;
import org.xml.sax.SAXParseException;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class JingGate {
    public static final Path DOCBOOK_RNC = Path.of("target/schema/docbookxi.rnc");
    public static final Path XHTML5_RNC  = Path.of("src/main/resources/schema/xhtml5/html5/xhtml5.rnc");

    public static List<String> validate(Path schemaRnc, Path xmlFile) {
        List<String> errors = new ArrayList<>();
        ErrorHandler eh = new ErrorHandler() {
            public void warning(SAXParseException e) { /* warnings are not gate failures */ }
            public void error(SAXParseException e) { errors.add(fmt(e)); }
            public void fatalError(SAXParseException e) { errors.add(fmt(e)); }
            private String fmt(SAXParseException e) {
                return e.getLineNumber() + ":" + e.getColumnNumber() + ": " + e.getMessage();
            }
        };
        try {
            var b = new PropertyMapBuilder();
            b.put(ValidateProperty.ERROR_HANDLER, eh);
            var driver = new ValidationDriver(b.toPropertyMap(), CompactSchemaReader.getInstance());
            if (!driver.loadSchema(ValidationDriver.fileInputSource(schemaRnc.toFile())))
                throw new IllegalStateException("schema failed to compile: " + schemaRnc + " " + errors);
            driver.validate(ValidationDriver.fileInputSource(xmlFile.toFile()));
        } catch (IllegalStateException e) {
            throw e;
        } catch (Exception e) {
            errors.add("0:0: " + e);
        }
        return errors;
    }
    private JingGate() {}
}
