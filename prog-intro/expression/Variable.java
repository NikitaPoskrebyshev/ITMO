package expression;

import java.math.BigInteger;

public class Variable extends AbstractValue {

    public Variable(final String v) {
        super(v);
    }

    @Override
    public int evaluate(final int x) {
        return x;
    }

    @Override
    public int evaluate(final int x, final int y, final int z) {
        return switch (this.v) {
            case "y" -> y;
            case "z" -> z;
            default -> x;
        };
    }
    @Override
    public BigInteger evaluate(final BigInteger x) {
        return x;
    }
}
