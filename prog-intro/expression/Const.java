package expression;

import java.math.BigInteger;

public class Const extends AbstractValue {
    public Const(final int v) {
        super(v);
    }
    public Const(final BigInteger v) {
        super(v);
    }

    @Override
    public int evaluate(final int x) {
        return Integer.parseInt(this.v);
    }

    @Override
    public int evaluate(final int x, final int y, final int z) {
        return Integer.parseInt(this.v);
    }
    @Override
    public BigInteger evaluate(final BigInteger x) {
        return new BigInteger(this.v);
    }
}
