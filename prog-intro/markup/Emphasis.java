package markup;

import java.util.List;

public class Emphasis extends AbstractVisualizationItem {
    public Emphasis(final List<VisualizationItem> inputText) {
        super(inputText);
    }

    @Override
    public void toMarkdown(StringBuilder s) {
        s.append("*");
        super.toMarkdown(s);
        s.append("*");
    }

    @Override
    public void toBBCode(StringBuilder s) {
        s.append("[i]");
        super.toBBCode(s);
        s.append("[/i]");
    }
}
