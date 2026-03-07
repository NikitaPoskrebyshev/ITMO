package game;

import java.io.PrintStream;
import java.util.Scanner;

public class HumanPlayer implements Player {
    private final PrintStream out;
    private final Scanner in;

    public HumanPlayer(final PrintStream out, final Scanner in) {
        this.out = out;
        this.in = in;
    }

    public HumanPlayer() {
        this(System.out, new Scanner(System.in));
    }

    @Override
    public Move move(final Position position, final Cell cell) {
        while (true) {
            out.println(position + "\n");
            out.println(cell + "'s move");
            out.println("Enter row and column");
            String rStr = in.next();
            String cStr = in.next();
            try {
                final Move move = new Move(Integer.parseInt(rStr), Integer.parseInt(cStr), cell);
                System.out.println();
                if (position.isValid(move)) {
                    return move;
                }
                final int row = move.getRow();
                final int column = move.getColumn();
                out.println("Move " + move + " is invalid\n");
            } catch (NumberFormatException e) {
                out.println("Wrong move numbers! Please, enter two integer numbers\n");
            }
        }
    }
}
