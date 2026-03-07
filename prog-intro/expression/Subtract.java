package expression;

public class Subtract extends AbstractOp {
    public Subtract(Expression value1, Expression value2) {
        super(value1, value2);
        op = Operation.SUBTRACT;
    }
}
