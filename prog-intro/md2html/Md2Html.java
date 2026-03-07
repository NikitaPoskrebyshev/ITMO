package md2html;

import java.io.BufferedWriter;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.UnsupportedEncodingException;
import java.lang.reflect.Array;
import java.util.*;

public class Md2Html {

    private enum SYMBOL {
        STRONG, EMPH, TXT, PRE, STRIKE, CODE, BACKSLASH, HEAD
    }

    private static SYMBOL checkSymbol(String line, int pos) {
        int n = line.length();
        boolean b = (pos != n - 1 && line.charAt(pos + 1) != ' ') ||
                (pos != 0 && line.charAt(pos - 1) != ' ');
        if (line.charAt(pos) == '*' || line.charAt(pos) == '_') {
            if (pos != n - 1 && (line.charAt(pos + 1) == '*' || line.charAt(pos + 1) == '_')) {
                return SYMBOL.STRONG;
            }
            if (b) {
                return SYMBOL.EMPH;
            }
            return SYMBOL.TXT;
        } else if (line.charAt(pos) == '-') {
            if (pos == n - 1 || line.charAt(pos + 1) != '-') {
                return SYMBOL.TXT;
            }
            return SYMBOL.STRIKE;
        } else if (line.charAt(pos) == '`') {
            if (pos <= n - 2 && line.charAt(pos + 1) == '`' && line.charAt(pos + 2) == '`') {
                return SYMBOL.PRE;
            }
            if (b) {
                return SYMBOL.CODE;
            }
            return SYMBOL.TXT;
        } else if (line.charAt(pos) == '\\') {
            return SYMBOL.BACKSLASH;
        }
        return SYMBOL.TXT;
    }

    private static void mapFill(Map<SYMBOL, List<String>> emphPaste, Map<SYMBOL, Boolean> emphType) {
        emphPaste.put(SYMBOL.EMPH, new ArrayList<>(List.of("<em>", "</em>")));
        emphPaste.put(SYMBOL.STRONG, new ArrayList<>(List.of("<strong>", "</strong>")));
        emphPaste.put(SYMBOL.STRIKE, new ArrayList<>(List.of("<s>", "</s>")));
        emphPaste.put(SYMBOL.CODE, new ArrayList<>(List.of("<code>", "</code>")));
        emphPaste.put(SYMBOL.PRE, new ArrayList<>(List.of("<pre>", "</pre>")));
        emphType.put(SYMBOL.EMPH, false);
        emphType.put(SYMBOL.STRONG, false);
        emphType.put(SYMBOL.STRIKE, false);
        emphType.put(SYMBOL.CODE, false);
        emphType.put(SYMBOL.HEAD, false);
        emphType.put(SYMBOL.PRE, false);
    }

    private static int posShift(SYMBOL type, int pos) {
        if (SYMBOL.EMPH.equals(type) || SYMBOL.CODE.equals(type) || SYMBOL.TXT.equals(type)) {
            return pos + 1;
        }
        if (SYMBOL.STRIKE.equals(type) || SYMBOL.STRONG.equals(type)) {
            return pos + 2;
        }
        return pos + 3;
    }

    private static String symbolRefactor(char c) {
        switch (c) {
            case '<':
                return "&lt;";
            case '>':
                return "&gt;";
            case '&':
                return "&amp;";
            default:
                return String.valueOf(c);
        }
    }

    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Invalid number of arguments");
            return;
        }
        try {
            Scanner in = new Scanner(new FileInputStream(args[0]));

            try {
                BufferedWriter out = new BufferedWriter(new OutputStreamWriter(
                        new FileOutputStream(args[1]),
                        "UTF-8"
                ));

                try {
                    Map<SYMBOL, List<String>> emphPaste = new HashMap<>();
                    Map<SYMBOL, Boolean> emphType = new HashMap<>();
                    mapFill(emphPaste, emphType);
                    int headType = 0;
                    boolean paragIsRunning = false;

                    while (in.hasNextLine()) {
                        String line = in.nextLine();
                        int n = line.length();
                        int pos = 0;

                        if (n == 0) {
                            if (emphType.get(SYMBOL.HEAD)) {
                                out.write("</h" + headType + ">\n");
                                headType = 0;
                            } else {
                                if (paragIsRunning) {
                                    out.write("</p>\n");
                                }
                            }
                            mapFill(emphPaste, emphType);
                            paragIsRunning = false;
                            continue;
                        }
                        if (!paragIsRunning) {
                            while (pos != n && line.charAt(pos) == '#') {
                                pos++;
                            }
                            if (pos != 0 && pos != n && line.charAt(pos) == ' ') {
                                emphType.put(SYMBOL.HEAD, true);
                            } else {
                                pos = 0;
                            }
                            headType = pos;
                            if (emphType.get(SYMBOL.HEAD)) {
                                out.write("<h" + headType + ">");
                                pos++;
                            } else {
                                out.write("<p>");
                            }
                            paragIsRunning = true;
                        } else {
                            out.write('\n');
                        }

                        while (pos < n) {
                            SYMBOL type = checkSymbol(line, pos);
                            if (type.equals(SYMBOL.TXT)) {
                                char c = line.charAt(pos);
                                String add = symbolRefactor(c);
                                out.write(add);
                                pos++;
                                continue;
                            }
                            if (type.equals(SYMBOL.BACKSLASH)) {
                                out.write(line.charAt(pos + 1));
                                pos += 2;
                                continue;
                            }
                            if (!emphType.get(SYMBOL.PRE) || type.equals(SYMBOL.PRE)) {
                                if (emphType.get(type)) {
                                    out.write(emphPaste.get(type).get(1));
                                } else {
                                    out.write(emphPaste.get(type).get(0));
                                }
                                emphType.put(type, !emphType.get(type));
                                pos = posShift(type, pos);
                            } else {
                                out.write(line.charAt(pos));
                                pos++;
                            }
                        }

                        if (!in.hasNextLine()) {
                            if (emphType.get(SYMBOL.HEAD)) {
                                out.write("</h" + headType + ">");
                                headType = 0;
                            } else {
                                out.write("</p>\n");
                            }
                        }
                    }
                } finally {
                    out.close();
                }

            } catch (FileNotFoundException e) {
                System.out.println("File with such name not found: " + e.getMessage());
            } catch (InputMismatchException e) {
                System.out.println("Invalid input data: " + e.getMessage());
            } catch (UnsupportedEncodingException e) {
                System.out.println("Unsupported encoding: " + e.getMessage());
            } catch (IOException e) {
                System.out.println("IOException has occured: " + e.getMessage());
            } finally {
                in.close();
            }
        } catch (FileNotFoundException e) {
            System.out.println("File with such name not found: " + e.getMessage());
        } catch (InputMismatchException e) {
            System.out.println("Invalid input data: " + e.getMessage());
        }
    }
}
