package markup;

public class Text implements VisualizationItem {
    String text;

    public Text(final String inputText) {
        this.text = inputText;
    }

    @Override
    public void toMarkdown(StringBuilder s) {
        s.append(text);
    }

    @Override
    public void toBBCode(StringBuilder s) {
        s.append(text);
    }
}
