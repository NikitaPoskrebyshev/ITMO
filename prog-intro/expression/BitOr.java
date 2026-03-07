package expression;

public class BitOr extends AbstractOp {
    public BitOr(Expression value1, Expression value2) {
        super(value1, value2);
        op = Operation.BITOR;
    }
}
