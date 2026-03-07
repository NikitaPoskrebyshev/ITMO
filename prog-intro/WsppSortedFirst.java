import java.io.*;
import java.util.*;

public class WsppSortedFirst {

    private static boolean checkSymbol(char c) {
        return (Character.getType(c) == Character.DASH_PUNCTUATION ||
                c == '\'' || Character.isLetter(c));
    }

    public static void main(String args[]) {
        if (args.length != 2) {
            System.out.println("Invalid number of file arguments");
            return;
        }
        try {
            MyScanner in = new MyScanner(new FileInputStream(args[0]));

            try {
                BufferedWriter out = new BufferedWriter(new OutputStreamWriter(
                        new FileOutputStream(args[1]),
                        "UTF-8"
                ));

                try {
                    TreeMap<String, Integer> used = new TreeMap<>();
                    HashMap<String, IntList> wordId = new HashMap<>();
                    int k = 1;

                    while (in.hasNextLine()) {
                        String line = in.nextLine();
                        line = line.toLowerCase();
                        int s = line.length();

                        StringBuilder finalWord = new StringBuilder();
                        HashMap<String, Boolean> usedInLine = new HashMap<>();

                        int l = 0;
                        while (l <= s) {
                            if (l != s && checkSymbol(line.charAt(l))) {
                                finalWord.append(line.charAt(l));
                            } else {
                                String finalWordString = finalWord.toString();

                                if (!finalWordString.isEmpty()) {
                                    int curAns = used.getOrDefault(finalWordString, 0);
                                    used.put(finalWordString, curAns + 1);

                                    if (!wordId.containsKey(finalWordString)) {
                                        wordId.put(finalWordString, new IntList());
                                    }
                                    if (!usedInLine.containsKey(finalWordString)) {
                                        wordId.get(finalWordString).add(k);
                                        usedInLine.put(finalWordString, true);
                                    }
                                    k++;
                                }
                                finalWord = new StringBuilder();
                            }
                            l++;
                        }
                    }

                    for (Map.Entry<String, Integer> entry : used.entrySet()) {
                        String slovo = entry.getKey();
                        int amount = entry.getValue();
                        out.write(slovo + " " + amount + " ");

                        IntList curWordId = wordId.get(slovo);
                        int sz = curWordId.size();

                        for (int i = 0; i < sz; i++) {
                            out.write(Integer.toString(curWordId.get(i)));
                            if (i != sz - 1) {
                                out.write(" ");
                            }
                        }
                        out.write("\n");
                    }
                } finally {
                    out.close();
                }

            } catch (FileNotFoundException e) {
                System.out.println("File with such name is not found: " + e.getMessage());
            } catch (UnsupportedEncodingException e) {
                System.out.println("Unsupported encoding: " + e.getMessage());
            } catch (InputMismatchException e) {
                System.out.println("Invalid input data: " + e.getMessage());
            } catch (IOException e) {
                System.out.println("IOException has occured: " + e.getMessage());
            } finally {
                in.close();
            }
        } catch (FileNotFoundException e) {
            System.out.println("File with such name is not found: " + e.getMessage());
        } catch (InputMismatchException e) {
            System.out.println("Invalid input data: " + e.getMessage());
        } catch (IOException e) {
            System.out.println("IOException has occured: " + e.getMessage());
        }
    }
}
