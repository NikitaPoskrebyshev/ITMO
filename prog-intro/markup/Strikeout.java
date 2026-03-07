package markup;

import java.util.List;

public class Strikeout extends AbstractVisualizationItem {
    public Strikeout(final List<VisualizationItem> inputText) {
        super(inputText);
    }

    @Override
    public void toMarkdown(StringBuilder s) {
        s.append("~");
        super.toMarkdown(s);
        s.append("~");
    }

    @Override
    public void toBBCode(StringBuilder s) {
        s.append("[s]");
        super.toBBCode(s);
        s.append("[/s]");
    }
}
