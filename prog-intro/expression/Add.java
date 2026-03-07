package expression;

public class Add extends AbstractOp {
    public Add(Expression value1, Expression value2) {
        super(value1, value2);
        op = Operation.ADD;
    }
}
