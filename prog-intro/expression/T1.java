package expression;

import java.math.BigInteger;

public class T1 extends AbstractUnOp {

    public T1(Expression G) {
        super(G);
        this.Op = UnOperation.T1;
    }

    @Override
    public BigInteger evaluate(BigInteger x) {
        return null;
    }

    @Override
    public int evaluate(int x) {
        int result = g.evaluate(x);
        int ans = 0;
        for (int d = 0; d < 32; d++) {
            if ((result >> d) % 2 == 0) {
                break;
            }
            ans++;
        }
        return ans;
    }

    public int evaluate(int x, int y, int z) {
        int result = g.evaluate(x, y, z);
        int ans = 0;
        for (int d = 0; d < 32; d++) {
            if ((result >> d) % 2 == 0) {
                break;
            }
            ans++;
        }
        return ans;
    }
}
