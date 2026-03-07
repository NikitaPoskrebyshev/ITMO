package markup;

import java.util.List;

public abstract class AbstractList implements PosListItem {
    List<ListItem> elements;

    public AbstractList(List<ListItem> inputElements) {
        this.elements = inputElements;
    }

    @Override
    public void toBBCode(final StringBuilder s) {
        for (ListItem it : elements) {
            it.toBBCode(s);
        }
    }
}
