package expression;

public class Divide extends AbstractOp {
    public Divide(Expression value1, Expression value2) {
        super(value1, value2);
        op = Operation.DIVIDE;
    }
}
