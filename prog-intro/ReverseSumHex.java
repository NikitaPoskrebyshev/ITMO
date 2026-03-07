import java.io.IOException;
import java.util.Scanner;
import java.util.Arrays;

public class ReverseSumHex {

    private static int[] resize(int[] mas) {
        return Arrays.copyOf(mas, 2 * mas.length);
    }

    public static void main(String[] args) {

        try {
            MyScanner in = new MyScanner(System.in);

            int[] smPref = new int[1];
            int szPref = 0;

            while (in.hasNextLine()) {
                MyScanner inNum = new MyScanner(in.nextLine());

                int[] smCur = new int[1];
                int[] lineCur = new int[1];
                int sz = 0;

                while (inNum.hasNext()) {
                    int num = Integer.parseUnsignedInt(inNum.next(), 16);

                    if (sz == lineCur.length) {
                        lineCur = resize(lineCur);
                        smCur = resize(smCur);
                    }

                    lineCur[sz] = num;
                    sz++;

                    if (szPref == smPref.length) {
                        smPref = resize(smPref);
                    }
                    szPref++;
                }
                inNum.close();

                for (int i = 0; i < sz; i++) {
                    smCur[i] += smPref[i] + lineCur[i];
                    smPref[i] += lineCur[i];
                }
                for (int i = 1; i < sz; i++) {
                    smCur[i] += smCur[i - 1];
                }

                for (int i = 0; i < sz; i++) {
                    System.out.print(Integer.toHexString(smCur[i]));
                    System.out.print(" ");
                }
                System.out.println();
            }

            in.close();
        } catch (IOException e) {
            System.out.println("IOException occurred: " + e.getMessage());
        }

    }
}
