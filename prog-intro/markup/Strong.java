package markup;

import java.util.List;

public class Strong extends AbstractVisualizationItem {
    public Strong(final List<VisualizationItem> inputText) {
        super(inputText);
    }

    @Override
    public void toMarkdown(StringBuilder s) {
        s.append("__");
        super.toMarkdown(s);
        s.append("__");
    }

    @Override
    public void toBBCode(StringBuilder s) {
        s.append("[b]");
        super.toBBCode(s);
        s.append("[/b]");
    }
}
