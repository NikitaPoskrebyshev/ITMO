package expression.parser;

import expression.*;

public class ExpressionParser implements TripleParser {

    public ExpressionParser() {
    }

    public GlobalExpression parse(final String expression) {
        return new ExpParser(new StringSource(expression)).parseExpression();
    }

    private static class ExpParser extends BaseParser {
        public ExpParser(final CharSource source) {
            super(source);
        }

        public GlobalExpression parseExpression() {
            final GlobalExpression result = parseOr();
            if (eof()) {
                return result;
            }
            throw error("End of Expression expected");
        }

        private GlobalExpression parseOr() {
            skipWhitespace();
            GlobalExpression result = parseXor();
            skipWhitespace();

            while (!eof()) {
                if (take('|')) {
                    result = new BitOr(result, parseXor());
                    skipWhitespace();
                } else {
                    break;
                }
            }
            skipWhitespace();

            return result;
        }

        private GlobalExpression parseXor() {
            skipWhitespace();
            GlobalExpression result = parseAnd();
            skipWhitespace();

            while (!eof()) {
                if (take('^')) {
                    result = new BitXor(result, parseAnd());
                    skipWhitespace();
                } else {
                    break;
                }
            }
            skipWhitespace();

            return result;
        }

        private GlobalExpression parseAnd() {
            skipWhitespace();
            GlobalExpression result = parse();
            skipWhitespace();

            while (!eof()) {
                if (take('&')) {
                    result = new BitAnd(result, parse());
                    skipWhitespace();
                } else {
                    break;
                }
            }
            skipWhitespace();

            return result;
        }

        private GlobalExpression parse() {
            skipWhitespace();
            GlobalExpression result = parsePlusMinus();
            skipWhitespace();

            while (!eof()) {
                if (take('+')) {
                    result = new Add(result, parsePlusMinus());
                    skipWhitespace();
                } else if (take('-')) {
                    result = new Subtract(result, parsePlusMinus());
                    skipWhitespace();
                } else {
                    skipWhitespace();
                    break;
                }
            }
            skipWhitespace();

            return result;
        }

        private GlobalExpression parseMulDiv() {
            skipWhitespace();
            if (take('-')) {
                if (between('0', '9')) {
                    return parseConst(true);
                }
                return new UnMinus(parseMulDiv());
            } else {
                if (take('l')) {
                    take('1');
                    return new L1(parseMulDiv());
                } else if (take('t')) {
                    take('1');
                    return new T1(parseMulDiv());
                } else if (between('0', '9')) {
                    return parseConst(false);
                } else if (between('x', 'z')) {
                    return parseVariable();
                } else {
                    take('(');
                    GlobalExpression result = parseOr();
                    skipWhitespace();
                    take(')');
                    skipWhitespace();
                    return result;
                }
            }
        }

        private GlobalExpression parsePlusMinus() {
            skipWhitespace();
            GlobalExpression result = parseMulDiv();
            skipWhitespace();

            while (!eof()) {
                if (take('*')) {
                    result = new Multiply(result, parseMulDiv());
                    skipWhitespace();
                } else if (take('/')) {
                    result = new Divide(result, parseMulDiv());
                    skipWhitespace();
                } else {
                    break;
                }
            }

            skipWhitespace();
            return result;
        }

        private GlobalExpression parseVariable() {
            skipWhitespace();
            if (take('x')) {
                return new Variable("x");
            } else if (take('y')) {
                return new Variable("y");
            } else {
                take('z');
                return new Variable("z");
            }
        }

        private GlobalExpression parseConst(boolean isNeg) {
            skipWhitespace();
            StringBuilder sb = new StringBuilder();
            if (isNeg) {
                sb.append('-');
            }
            takeInteger(sb);
            return new Const(Integer.parseInt(sb.toString()));
        }

        private void takeInteger(final StringBuilder sb) {
            if (take('0')) {
                sb.append('0');
            } else if (between('1', '9')) {
                takeDigits(sb);
            } else {
                throw error("Invalid number");
            }
        }

        private void takeDigits(final StringBuilder sb) {
            while (between('0', '9')) {
                sb.append(take());
            }
        }

        private void skipWhitespace() {
            while (Character.isWhitespace(ch)) {
                take();
            }
        }
    }
}
