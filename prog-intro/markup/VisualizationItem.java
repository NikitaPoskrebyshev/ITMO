package markup;

public interface VisualizationItem {
    void toMarkdown(StringBuilder s);
    void toBBCode(StringBuilder s);
}
