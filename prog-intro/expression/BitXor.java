package expression;

public class BitXor extends AbstractOp {
    public BitXor(Expression value1, Expression value2) {
        super(value1, value2);
        op = Operation.BITXOR;
    }
}
