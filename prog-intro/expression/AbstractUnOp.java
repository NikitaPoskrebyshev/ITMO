package expression;

import java.math.BigInteger;

public abstract class AbstractUnOp implements GlobalExpression {
    protected final GlobalExpression g;
    protected UnOperation Op;

    public AbstractUnOp(Expression G) {
        this.g = (GlobalExpression) G;
    }

    public BigInteger evaluate(BigInteger x) {
        return null;
    }

    private String opToString() {
        return switch (Op) {
            case UNMINUS -> "-";
            case L1 -> "l1";
            case T1 -> "t1";
        };
    }

    public String toMiniString(Operation operation, boolean isRight) {
        if (g.getClass() == Variable.class || g.getClass() == Const.class ||
                g.getClass() == UnMinus.class || g.getClass() == L1.class || g.getClass() == T1.class) {
            return opToString() + ' ' + g.toMiniString();
        }
        return opToString() + '(' + g.toMiniString() + ')';
    }

    public String toMiniString() {
        return toMiniString(Operation.ADD, false);
    }

    public String toString() {
        return opToString() + '(' + g.toString() + ")";
    }
}