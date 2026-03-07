package expression;

public class BitAnd extends AbstractOp {
    public BitAnd(Expression value1, Expression value2) {
        super(value1, value2);
        op = Operation.BITAND;
    }
}
