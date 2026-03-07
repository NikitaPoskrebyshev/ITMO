package expression;

import java.math.BigInteger;

public class L1 extends AbstractUnOp {

    public L1(Expression G) {
        super(G);
        this.Op = UnOperation.L1;
    }

    @Override
    public BigInteger evaluate(BigInteger x) {
        return null;
    }

    @Override
    public int evaluate(int x) {
        int result = g.evaluate(x);
        if (result > 0) {
            return 0;
        }
        int ans = 0;
        for (int d = 31; d >= 0; d--) {
            if ((result >> d) % 2 == 0) {
                break;
            }
            ans++;
        }
        return ans;
    }

    public int evaluate(int x, int y, int z) {
        int result = g.evaluate(x, y, z);
        if (result > 0) {
            return 0;
        }
        int ans = 0;
        for (int d = 31; d >= 0; d--) {
            if ((result >> d) % 2 == 0) {
                break;
            }
            ans++;
        }
        return ans;
    }
}
