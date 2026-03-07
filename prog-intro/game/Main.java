package game;

import java.text.CollationElementIterator;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.TreeMap;
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);

        System.out.println("\nWelcome to mnk-game!\n");
        System.out.println("Please, choose the game mode you want to play:\n");
        System.out.println("Regular game - enter 1\nChampionship - enter 2\n");

        int gameModeNum = 1;
        GameMode gameMode = GameMode.REGULAR;
        int boardTypeNum = 1;
        MNKgameBoardType boardType = MNKgameBoardType.CLASSIC;
        int m = 3, n = 3, k = 3, d = 10;

        boolean gameLoadSuccess = false;
        while (!gameLoadSuccess) {
            System.out.print("Game mode: ");
            String gameModeStr = in.nextLine();
            try {
                gameModeNum = Integer.parseInt(gameModeStr);
                switch (gameModeNum) {
                case 1:
                    gameMode = GameMode.REGULAR;
                    break;
                case 2:
                    gameMode = GameMode.CHAMPIONSHIP;
                    break;
                default:
                    System.out.println("Wrong game mode! Please, enter 1(Regular game) or 2(Championship)\n");
                    gameLoadSuccess = false;
                    break;
            }
                gameLoadSuccess = true;
                break;
            } catch (NumberFormatException e) {
                System.out.println("Wrong game mode! Please, enter 1(Regular game) or 2(Championship)\n");
            }
        }

        System.out.println("Please, choose the board type you want to play on:\n");
        System.out.println("Classic - enter 1\nCircle - enter 2\n");

        gameLoadSuccess = false;
        while (!gameLoadSuccess) {
            System.out.print("Board type: ");
            String boardTypeNumStr = in.nextLine();
            try {
                boardTypeNum = Integer.parseInt(boardTypeNumStr);
                if (gameModeNum != 1 && gameModeNum != 2) {
                    System.out.println("Wrong board type! Please, enter 1 (classic board) or 2 (circle board)\n");
                    continue;
                }
                gameLoadSuccess = true;
            } catch (NumberFormatException e) {
                System.out.println("Wrong board type! Please, enter 1 (classic board) or 2 (circle board)\n");
            }

            switch (boardTypeNum) {
                case 1:
                    boardType = MNKgameBoardType.CLASSIC;
                    break;
                case 2:
                    boardType = MNKgameBoardType.CIRCLE;
                    break;
                default:
                    System.out.println("Wrong board type! Please, enter 1 (classic board) or 2 (circle board)\n");
                    gameLoadSuccess = false;
                    break;
            }
        }

        gameLoadSuccess = false;
        while (!gameLoadSuccess) {
            String kStr;
            switch (boardType) {
                case CLASSIC:
                    System.out.println("Now enter m, n and k values:\n");
                    System.out.print("m: ");
                    String mStr = in.nextLine();
                    System.out.print("n: ");
                    String nStr = in.nextLine();
                    System.out.print("k: ");
                    kStr = in.nextLine();
                    try {
                        m = Integer.parseInt(mStr);
                        n = Integer.parseInt(nStr);
                        k = Integer.parseInt(kStr);
                        gameLoadSuccess = true;
                        break;
                    } catch (NumberFormatException e) {
                        System.out.println("Wrong m n k numbers! Please, enter three integer numbers in three lines\n");
                    }
                    break;
                case CIRCLE:
                    System.out.println("Now enter diameter of a circle and k number: ");
                    System.out.print("Diameter: ");
                    String dStr = in.nextLine();
                    System.out.print("k: ");
                    kStr = in.nextLine();
                    try {
                        d = Integer.parseInt(dStr);
                        k = Integer.parseInt(kStr);
                        m = d;
                        n = d;
                        gameLoadSuccess = true;
                        break;
                    } catch (NumberFormatException e) {
                        System.out.println("Wrong diameter value! Please, enter single integer number\n");
                    }
                    break;
                default:
                    break;
            }
        }


        switch (gameMode) {
            case REGULAR:
                final Game game = new Game(false, new HumanPlayer(), new HumanPlayer());
                int result;
                do {
                    System.out.println("The game has started!\n");
                    result = game.play(new MNKgameBoard(m, n, k, boardType));
                    switch (result) {
                        case 1:
                            System.out.println("Player1 won!");
                            break;
                        case 2:
                            System.out.println("Player2 won!");
                            break;
                        default:
                            System.out.println("Draw");
                            break;
                    }
                    System.out.println("\nDo you want to continue?\n");
                    System.out.println("Yes - enter 1\nNo - enter 2\n");
                    int choise = in.nextInt();
                    if (choise == 2) {
                        break;
                    }
                } while (true);
                break;
            case CHAMPIONSHIP:
                int participantsNum = 0;
                System.out.print("Enter the number of players you want to play against: ");
                while (true) {
                    String participantsStr = in.nextLine();
                    try {
                        participantsNum = Integer.parseInt(participantsStr) + 1;
                        break;
                    } catch (NumberFormatException e) {
                        System.out.print("Wrong number of players! Please, enter a single number: ");
                    }
                }
                
                ArrayList<Player> players = new ArrayList<>();
                ArrayList<ArrayList<Integer>> leaderBoard = new ArrayList<>();
                for (int i = 0; i < participantsNum; i++) {
                    leaderBoard.add(new ArrayList<>());
                }
                int round = 0;
                players.add(new HumanPlayer());

                for (int i = 0; i < participantsNum - 1; i++) {
                    players.add(new RandomPlayer(m, n));
                }

                HashMap<Player, Integer> playersNum = new HashMap<>();
                for (int i = 0; i < participantsNum; i++) {
                    playersNum.put(players.get(i), i + 1);
                }

                while (participantsNum > 1) {
                    ArrayList<Player> nextLvl = new ArrayList<>();
                    ArrayList<Boolean> used = new ArrayList<>();
                    for (int i = 0; i < participantsNum; i++) {
                        used.add(false);
                    }
                    int curLvlAmount = (int)Math.pow(2, Math.floor(Math.log(participantsNum) / Math.log(2)));                                                                                                               

                    int f = 0, s = 0;
                    while (f < curLvlAmount) {
                        if (!used.get(f)) {
                            s = f + 1;
                            while (s < curLvlAmount) {
                                if (!used.get(s)) {
                                    used.set(f, true);
                                    used.set(s, true);
                                    final Game curGame = new Game(false, players.get(f), players.get(s));
                                    int res;
                                    do {
                                        res = curGame.play(new MNKgameBoard(m, n, k, boardType));
                                        switch (res) {
                                            case 1:
                                                nextLvl.add(players.get(f));
                                                leaderBoard.get(round).add(playersNum.get(players.get(s)));
                                                break;
                                            case 2:
                                                nextLvl.add(players.get(s));
                                                leaderBoard.get(round).add(playersNum.get(players.get(f)));
                                                break;
                                        default:
                                            break;
                                        }
                                        if (res == 1 || res == 2) {
                                            break;
                                        }
                                    } while(true);
                                    break;
                                }
                                s++;
                            }
                        }
                        f++;
                    }
                    
                    for (int i = curLvlAmount; i < participantsNum; i++) {
                        nextLvl.add(players.get(i));
                    }
                    round++;
                    players = nextLvl;
                    participantsNum = participantsNum - curLvlAmount + curLvlAmount / 2;
                }

                leaderBoard.get(round).add(playersNum.get(players.get(0)));
                for (int i = round; i >= 0; i--) {
                    System.out.print(round - i + 1 + " place: ");
                    for (int c : leaderBoard.get(i)) {
                        System.out.print(c + " ");
                    }
                    System.out.println();
                }
                break;
            default:
                break;
        }
        
        in.close();
    }
}
