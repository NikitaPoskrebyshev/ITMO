import java.io.IOException;
import java.util.ArrayList;
import java.util.InputMismatchException;
import java.util.Scanner;

public class Reverse {
    public static void main(String[] args) {
        try {
            MyScanner in = new MyScanner(System.in);
            ArrayList<String> mas = new ArrayList<>();

            while(in.hasNextLine()){
                mas.add(in.nextLine());
            }
//            System.err.println(mas.size());
            for (var c : mas) {
//                System.err.println(c);
            }

            for(int i = mas.size() - 1; i >= 0; i--){
                ArrayList<String> cur_line = new ArrayList<>();
                int l = 0;
                String s = mas.get(i);
                for(int j = 0; j < s.length(); j++){
                    char c = s.charAt(j);
                    if(c == ' '){
                        if(j != l){
                            cur_line.add(s.substring(l, j));
                        }
                        l = j + 1;
                    }
                }
                if(l != s.length()){
                    cur_line.add(s.substring(l));
                }

                for(int j = cur_line.size() - 1; j >= 0; j--){
                    System.out.print(cur_line.get(j));
                    System.out.print(" ");
//                    System.err.print(cur_line.get(j));
//                    System.err.print(" ");
                }
                System.out.println();
//                System.err.println();
            }

            in.close();
        } catch (IOException e) {
            System.out.println("IOException occurred: " + e.getMessage());
        }
    }
}

/*
1         2         3

4         5
6
*/
