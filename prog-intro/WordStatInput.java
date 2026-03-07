import java.io.*;
import java.util.*;

public class WordStatInput {

    private static boolean checkSymbol(char c) {
        return (Character.getType(c) == Character.DASH_PUNCTUATION ||
                c == '\'' || Character.isLetter(c));
    }
    public static void main (String[] args) {
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
                    HashMap<String, Integer> used = new HashMap<>();
                    ArrayList<String> mas = new ArrayList<>();

                    while (in.hasNext()) {
                        String word = in.next();
                        word = word.toLowerCase();
                        int s = word.length();

                        StringBuilder finalWord = new StringBuilder();

                        int l = 0;
                        while (l <= s) {
                            if (l != s && checkSymbol(word.charAt(l))) {
                                finalWord.append(word.charAt(l));
                            }
                            else {
                                String otvetik = finalWord.toString();
                                if (!otvetik.isEmpty()) {
                                    int curAns = used.getOrDefault(otvetik, 0);
                                    if (curAns != 0) {
                                        used.put(otvetik, curAns + 1);
                                    }
                                    else {
                                        used.put(otvetik, 1);
                                        mas.add(otvetik);
                                    }
                                }
                                finalWord = new StringBuilder();
                            }
                            l++;
                        }
                    }
                    for (String c : mas) {
                        out.write(c + " " + used.get(c) + '\n');
                    }
                }
                finally {
                    out.close();
                }

            }
            catch (FileNotFoundException e) {
                System.out.println("File with such name is not found: " + e.getMessage());
            }
            catch (UnsupportedEncodingException e) {
                System.out.println("Unsupported encoding: " + e.getMessage());
            }
            catch (InputMismatchException e) {
                System.out.println("Invalid input data: " + e.getMessage());
            }
            catch (IOException e) {
                System.out.println("IOException has occured: " + e.getMessage());
            } finally {
                in.close();
            }
        }
        catch (FileNotFoundException e) {
            System.out.println("File with such name is not found: " + e.getMessage());
        }
        catch (InputMismatchException e) {
            System.out.println("Invalid input data: " + e.getMessage());
        }
        catch (IOException e) {
            System.out.println("IOException has occured: " + e.getMessage());
        }
    }
}