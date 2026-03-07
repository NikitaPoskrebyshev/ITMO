package markup;

import java.util.List;

public abstract class AbstractVisualizationItem implements VisualizationItem {
    protected List<VisualizationItem> text;

    public AbstractVisualizationItem(final List<VisualizationItem> inputText) {
        this.text = inputText;
    };

    @Override
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