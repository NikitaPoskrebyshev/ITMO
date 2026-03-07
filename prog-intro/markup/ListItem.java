package markup;

import java.util.List;

public class ListItem {
    protected List<PosListItem> elements;

    public ListItem(final List<PosListItem> inputElements) {
        this.elements = inputElements;
    }

    public void toBBCode(StringBuilder s) {
        s.append("[*]");
        for (PosListItem c : elements) {
            c.toBBCode(s);
        }
    }
}
