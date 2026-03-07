package game;

public class ProtectedBoard implements Board, Position {

    private final MNKgameBoard board;

    public ProtectedBoard(MNKgameBoard copyBoard) {
        this.board = copyBoard;
    }

    @Override
    public boolean isValid(Move move) {
        return board.isValid(move);
    }

    @Override
    public Cell getCell(int r, int c) {
        return board.getCell(r, c);
    }

    @Override
    public Position getPosition() {
        return this;
    }

    @Override
    public Cell getCell() {
        return board.getCell();
    }

    @Override
    public Result makeMove(Move move) {
        return board.makeMove(move);
    }
    
    @Override
    public String toString() {
        return board.toString();
    }
}
