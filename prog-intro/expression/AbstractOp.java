package expression;

import expression.common.Op;

import java.math.BigInteger;

public abstract class AbstractOp implements GlobalExpression {
    protected Operation op;
    protected final GlobalExpression exp1;
    protected final GlobalExpression exp2;

    public AbstractOp(final Expression value1, final Expression value2) {
        this.exp1 = (GlobalExpression) value1;
        this.exp2 = (GlobalExpression) value2;
    }

    private String opToString() {
        return switch (op) {
            case ADD -> " + ";
            case SUBTRACT -> " - ";
            case MULTIPLY -> " * ";
            case DIVIDE -> " / ";
            case BITAND -> " & ";
            case BITXOR -> " ^ ";
            case BITOR -> " | ";
        };
    }

    @Override
    public int evaluate(final int x) {
        return switch (op) {
            case ADD -> exp1.evaluate(x) + exp2.evaluate(x);
            case SUBTRACT -> exp1.evaluate(x) - exp2.evaluate(x);
            case MULTIPLY -> exp1.evaluate(x) * exp2.evaluate(x);
            case DIVIDE -> exp1.evaluate(x) / exp2.evaluate(x);
            case BITAND -> exp1.evaluate(x) & exp2.evaluate(x);
            case BITXOR -> exp1.evaluate(x) ^ exp2.evaluate(x);
            case BITOR -> exp1.evaluate(x) | exp2.evaluate(x);
        };
    }

    @Override
    public int evaluate(final int x, final int y, final int z) {
        return switch (op) {
            case ADD -> exp1.evaluate(x, y, z) + exp2.evaluate(x, y, z);
            case SUBTRACT -> exp1.evaluate(x, y, z) - exp2.evaluate(x, y, z);
            case MULTIPLY -> exp1.evaluate(x, y, z) * exp2.evaluate(x, y, z);
            case DIVIDE -> exp1.evaluate(x, y, z) / exp2.evaluate(x, y, z);
            case BITAND -> exp1.evaluate(x, y, z) & exp2.evaluate(x, y, z);
            case BITXOR -> exp1.evaluate(x, y, z) ^ exp2.evaluate(x, y, z);
            case BITOR -> exp1.evaluate(x, y, z) | exp2.evaluate(x, y, z);
        };
    }

    @Override
    public BigInteger evaluate(final BigInteger x) {
        return switch (op) {
            case ADD -> exp1.evaluate(x).add(exp2.evaluate(x));
            case SUBTRACT -> exp1.evaluate(x).subtract(exp2.evaluate(x));
            case MULTIPLY -> exp1.evaluate(x).multiply(exp2.evaluate(x));
            case DIVIDE -> exp1.evaluate(x).divide(exp2.evaluate(x));
            default -> null;
        };
    }

    @Override
    public boolean equals(final Object obj) {
        if (obj == null || this.getClass() != obj.getClass()) {
            return false;
        }
        AbstractOp objCopy = (AbstractOp) obj;
        return exp1.equals(objCopy.exp1) && exp2.equals(objCopy.exp2);
    }

    @Override
    public int hashCode() {
        final int B = 17;
        final int MOD = (int) 1e9 + 7;
        return ((exp1.hashCode() + B * B * B) % MOD + (opToString().hashCode() + B * B) % MOD + (exp2.hashCode() * B % MOD)) % MOD;
    }

    @Override
    public String toString() {
        return '(' + exp1.toString() + opToString() + exp2.toString() + ')';
    }

    private boolean checkBrackets(Operation prev, Operation cur, boolean isRight) {
        switch (prev) {
            case ADD -> {
                return (cur == Operation.BITOR ||
                        cur == Operation.BITXOR ||
                        cur == Operation.BITAND);
            }
            case SUBTRACT -> {
                return (cur == Operation.BITOR ||
                        cur == Operation.BITXOR ||
                        cur == Operation.BITAND ||
                        (isRight && (cur == Operation.ADD || cur == Operation.SUBTRACT)));
            }
            case MULTIPLY -> {
                if (cur == Operation.BITOR ||
                    cur == Operation.BITXOR ||
                    cur == Operation.BITAND) {
                    return true;
                }
                if (isRight) {
                    return cur != Operation.MULTIPLY;
                }
                return (cur == Operation.ADD || cur == Operation.SUBTRACT);
            }
            case DIVIDE -> {
                if (cur == Operation.BITOR ||
                        cur == Operation.BITXOR ||
                        cur == Operation.BITAND) {
                    return true;
                }
                if (isRight) {
                    return true;
                }
                return (cur == Operation.ADD || cur == Operation.SUBTRACT);
            }
            case BITOR -> {
                return false;
            }
            case BITXOR -> {
                return cur == Operation.BITOR;
            }
            case BITAND -> {
                return (cur == Operation.BITOR || cur == Operation.BITXOR);
            }
        }
        return false;
    }

    @Override
    public String toMiniString(Operation operation, boolean isRight) {
        if (!checkBrackets(operation, this.op, isRight)) {
            return exp1.toMiniString(this.op, false) + opToString() + exp2.toMiniString(this.op, true);
        }
        return '(' + exp1.toMiniString(this.op, false) + opToString() + exp2.toMiniString(this.op, true) + ')';
    }

    @Override
    public String toMiniString() {
        return exp1.toMiniString(this.op, false) + opToString() + exp2.toMiniString(this.op, true);
    }
}
