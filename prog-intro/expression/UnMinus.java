package expression;

import java.math.BigInteger;

public class UnMinus extends AbstractUnOp {

    public UnMinus(Expression G) {
        super(G);
        this.Op = UnOperation.UNMINUS;
    }

    @Override
    public BigInteger evaluate(BigInteger x) {
        return null;
    }

    @Override
    public int evaluate(int x) {
        return -1 * g.evaluate(x);
    }

    public int evaluate(int x, int y, int z) {
        return -1 * g.evaluate(x, y, z);
    }
}
