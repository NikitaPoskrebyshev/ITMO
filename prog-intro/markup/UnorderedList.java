package markup;

import java.util.List;

public class UnorderedList extends AbstractList{
    public UnorderedList(final List<ListItem> inputText) {
        super(inputText);
    }
    // :NOTE: добавление open- и close-tag можно было внести в абстрактный метод (везде)
    @Override
    public void toBBCode(StringBuilder s) {
        s.append("[list]");
        super.toBBCode(s);
        s.append("[/list]");
    }
}
