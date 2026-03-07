package game;

import java.util.Random;

public class RandomPlayer implements Player {
    private final Random random;
    private final int m;
    private final int n;

    public RandomPlayer(final Random random, final int M, final int N) {
        this.random = random;
        this.m = M;
        this.n = N;
    }

    public RandomPlayer(final int M, final int N) {
        this(new Random(), M, N);
    }

    @Override
    public Move move(final Position position, final Cell cell) {
        while (true) {
            int r = random.nextInt(m);
            int c = random.nextInt(n);
            final Move move = new Move(r, c, cell);
            if (position.isValid(move)) {
                return move;
            }
        }
    }
}