package game;

import java.util.Arrays;
import java.util.Map;

public class MNKgameBoard implements Board {

    private static final Map<Cell, Character> SYMBOLS = Map.of(
            Cell.X, 'X',
            Cell.O, 'O',
            Cell.E, '.',
            Cell.F, '#'
    );

    private final Cell[][] cells;
    private Cell turn;
    private final int m;
    private final int n;
    private final int k;
    private int usedCur;
    private int ableToUse;

    public MNKgameBoard(final int rows, final int columns, final int K, final MNKgameBoardType type) {
        this.m = rows;
        this.n = columns;
        this.k = K;
        this.cells = new Cell[rows][columns];
        this.ableToUse = 0;
        switch (type) {
            case CLASSIC:
                ableToUse = n * m;
                for (Cell[] row : cells) {
                    Arrays.fill(row, Cell.E);
                }
                turn = Cell.X;
                break;
            case CIRCLE:
                int center = rows / 2;
                for (int r = 0; r < rows; r++) {
                    for (int c = 0; c < columns; c++) {
                        if (Math.sqrt((r - center) * (r - center) + (c - center) * (c - center)) <= rows / 2) {
                            cells[r][c] = Cell.E;
                            ableToUse++;
                        }
                        else {
                            cells[r][c] = Cell.F;
                        }
                    }
                }
                turn = Cell.X;
                break;
            default:
                break;
        }
    }

    @Override
    public Position getPosition() {
        return new ProtectedBoard(this);
    }

    @Override
    public Cell getCell() {
        return turn;
    }

    public Cell getCell(final int r, final int c) {
        return cells[r][c];
    }

    @Override
    public Result makeMove(final Move move) {
        if (!isValid(move)) {
            return Result.LOSE;
        }
        
        usedCur++;
        int rCur = move.getRow();
        int cCur = move.getColumn();
        cells[rCur][cCur] = move.getValue();

        Result res = checkWin(rCur, cCur, usedCur);
        if (res == Result.UNKNOWNDOP) {
            System.out.println("Well played! You have an extra move!");
        }
        else {
            turn = turn == Cell.X ? Cell.O : Cell.X;
        }

        return res;
    }

    public boolean isValid(final Move move) {
        return 0 <= move.getRow() && move.getRow() < m
                && 0 <= move.getColumn() && move.getColumn() < n
                && cells[move.getRow()][move.getColumn()] == Cell.E
                && turn == getCell();
    }
    
    private Result checkWin(int rCur, int cCur, int usedCur) {

        boolean checkDop = true;
        boolean checkDopFinal = false;
        int r = rCur;
        int c = cCur;
        int check1 = 0;
        int check2 = 0;
        //horizontally
        while (c < n && cells[r][c] == turn) {
            check1++;
            c++;
        }
        if (check1 >= 4) {
            checkDop = false;
        }
        c = cCur - 1;
        while (c >= 0 && cells[r][c] == turn) {
            check2++;
            c--;
        }
        if (check2 >= 4) {
            checkDop = false;
        }

        if (check1 + check2 >= k) {
            return Result.WIN;
        }
        if (checkDop && check1 + check2 >= 4) {
            checkDopFinal = true;
        }

        r = rCur;
        c = cCur;
        check1 = 0;
        check2 = 0;
        checkDop = true;
        //vertically
        while (r < m && cells[r][c] == turn) {
            check1++;
            r++;
        }
        if (check1 >= 4) {
            checkDop = false;
        }
        r = rCur - 1;
        while (r >= 0 && cells[r][c] == turn) {
            check2++;
            r--;
        }
        if (check2 >= 4) {
            checkDop = false;
        }
        if (check1 + check2 >= k) {
            return Result.WIN;
        }
        if (checkDop && check1 + check2 >= 4) {
            checkDopFinal = true;
        }

        r = rCur;
        c = cCur;
        check1 = 0;
        check2 = 0;
        checkDop = true;
        //diagonally1
        while (r < m && c < n && cells[r][c] == turn) {
            check1++;
            r++;
            c++;
        }
        if (check1 >= 4) {
            checkDop = false;
        }
        r = rCur - 1;
        c = cCur - 1;
        while (r >= 0 && c >= 0 && cells[r][c] == turn) {
            check2++;
            r--;
            c--;
        }
        if (check2 >= 4) {
            checkDop = false;
        }
        if (check1 + check2 >= k) {
            return Result.WIN;
        }
        if (checkDop && check1 + check2 >= 4) {
            checkDopFinal = true;
        }

        r = rCur;
        c = cCur;
        check1 = 0;
        check2 = 0;
        checkDop = true;
        //diagonally2
        while (r < m && c >= 0 && cells[r][c] == turn) {
            check1++;
            r++;
            c--;
        }
        if (check1 >= 4) {
            checkDop = false;
        }
        r = rCur - 1;
        c = cCur + 1;
        while (r >= 0 && c < n && cells[r][c] == turn) {
            check2++;
            r--;
            c++;
        }
        if (check2 >= 4) {
            checkDop = false;
        }
        if (check1 + check2 >= k) {
            return Result.WIN;
        }
        if (checkDop && check1 + check2 >= 4) {
            checkDopFinal = true;
        }

        if (usedCur == ableToUse) {
            return Result.DRAW;
        }
        else {
            if (checkDopFinal) {
                return Result.UNKNOWNDOP;
            }
            return Result.UNKNOWN;
        }
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder(" ");
        for (int i = 0; i < n; i++) {
            sb.append(Integer.toString(i));
        }
        for (int r = 0; r < m; r++) {
            sb.append("\n");
            sb.append(r);
            for (int c = 0; c < n; c++) {
                sb.append(SYMBOLS.get(cells[r][c]));
            }
        }
        return sb.toString();
    }
}
