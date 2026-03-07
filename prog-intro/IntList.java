import java.util.Arrays;

public class IntList {
    private int sz;
    private int curAdd;
    private int a[];

    IntList() {
        this.sz = 1;
        this.curAdd = 0;
        this.a = new int[1];
    }

    private void resize() {
        sz *= 2;
        a = Arrays.copyOf(a, sz);
    }

    public int size() {
        return curAdd;
    }

    public int get(int id) throws ArrayIndexOutOfBoundsException {
        return a[id];
    }

    public void add(int v) {
        if (curAdd == sz) {
            resize();
        }
        a[curAdd] = v;
        curAdd++;
    }
}
