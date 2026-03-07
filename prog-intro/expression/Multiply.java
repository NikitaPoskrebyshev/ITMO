package expression;

public class Multiply extends AbstractOp {
    public Multiply(Expression value1, Expression value2) {
        super(value1, value2);
        op = Operation.MULTIPLY;
    }
}
