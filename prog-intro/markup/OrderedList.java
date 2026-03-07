package markup;

import java.util.List;

public class OrderedList extends AbstractList {
    public OrderedList(final List<ListItem> inputText) {
        super(inputText);
    }

    @Override
    public void toBBCode(StringBuilder s) {
        s.append("[list=1]");
        super.toBBCode(s);
        s.append("[/list]");
    }
}
