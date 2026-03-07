import java.io.*;
import java.util.*;

public class WordStatCountMiddleL {

    private static boolean checkSymbol(char c) {
        return (Character.getType(c) == Character.DASH_PUNCTUATION ||
                c == '\'' || Character.isLetter(c));
    }

    private static void wordCount(BufferedReader in, BufferedWriter out) throws IOException {
        HashMap<String, Integer> used = new HashMap<>();
        ArrayList<String> mas = new ArrayList<>();

        char[] buffer = new char[1024];
        int read = in.read(buffer);
        String wordSave = "";

        while (read >= 0) {
            String line = new String(buffer, 0, read);
            int len = read;
            read = in.read(buffer);

            int l = 0;
            int r = 0;
            
            while (r < len) {

                l = r;

                while (r < len && checkSymbol(line.charAt(r))) {
                    r++;
                }

                String word = (line.substring(l, r)).toLowerCase();

                wordSave += word;
                if (r < len || (r == len && (read < 0 || !checkSymbol(buffer[0])))) {
                    if (wordSave.length() >= 5) {

                        wordSave = wordSave.substring(2, wordSave.length() - 2);

                        int cur_ans = used.getOrDefault(wordSave, 0);
                        if (cur_ans != 0) {
                            used.put(wordSave, cur_ans + 1);
                        }
                        else {
                            used.put(wordSave, 1);
                            mas.add(wordSave);
                        }
                    }
                    wordSave = "";
                }
                
                r++;
            }
        }

        mas.sort(new Comparator<String>() {
            public int compare(String p, String q) {
                return used.get(p) - used.get(q);
            }
        });

        for (String c : mas) {
            out.write(c + " " + used.get(c) + '\n');
        }
    }

    public static void main (String[] args) {
        if (args.length != 2) {
            System.out.println("Invalid number of file arguments");
            return;
        }
        try {
            BufferedReader in = new BufferedReader(new InputStreamReader(
                new FileInputStream(args[0]),
                "UTF-8"
            ));

            try {
                BufferedWriter out = new BufferedWriter(new OutputStreamWriter(
                    new FileOutputStream(args[1]),
                    "UTF-8"
                ));

                try {
                    wordCount(in, out);
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
                System.out.println("IOException has occurred: " + e.getMessage());
            } finally {
                in.close();
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
            System.out.println("IOException has occurred: " + e.getMessage());
        }
    }
}
