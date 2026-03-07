package expression;

public interface GlobalExpression extends Expression, TripleExpression, BigIntegerExpression {
    boolean equals(Object obj);
    int hashCode();
    String toMiniString(Operation operation, boolean isRight);
}
