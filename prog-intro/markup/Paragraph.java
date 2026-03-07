package markup;

import java.util.List;

public class Paragraph implements PosListItem {
    List<VisualizationItem> text;
    public Paragraph(final List<VisualizationItem> inputText) {
        this.text = inputText;
    }

    public void toMarkdown(final StringBuilder s) {
        for (VisualizationItem it : text) {
            it.toMarkdown(s);
        }
    }

    @Override
    public void toBBCode(final StringBuilder s) {
        for (VisualizationItem it : text) {
            it.toBBCode(s);
        }
    }
}
