package expression;

import java.math.BigInteger;

public abstract class AbstractValue implements GlobalExpression {

    protected String v;

    public AbstractValue(final int value) {
        this.v = Integer.toString(value);
    }
    public AbstractValue(final String value) {
        this.v = value;
    }
    public AbstractValue(final BigInteger value) {
        this.v = value.toString();
    }

    @Override
    public boolean equals(final Object obj) {
        if (obj == null || this.getClass() != obj.getClass()) {
            return false;
        }
        return this.v.equals(obj.toString());
    }

    @Override
    public int hashCode() {
        return this.v.hashCode();
    }

    @Override
    public String toString() {
        return v;
    }
    @Override
    public String toMiniString(Operation operation, boolean isRight) {
        return v;
    }
}
