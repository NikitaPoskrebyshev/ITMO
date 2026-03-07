import java.util.Arrays;
import java.io.IOException;
import java.lang.StringBuilder;

public class ReverseSumHexAbc {

    private static int[] resize(int[] mas) {
        return Arrays.copyOf(mas, 2 * mas.length);
    }
    
    private static int toInt(String s) {
        if (s.charAt(0) == '0') {
            return Integer.parseUnsignedInt(s.substring(2), 16);
        }
        int ans = 0;
        int p = 1;
        int l = s.length() - 1;
        while (l >= 0 && s.charAt(l) != '-') {
            ans += (s.charAt(l) - (int)'a') * p;
            p *= 10;
            l--;
        }
        if (s.charAt(0) == '-') {
            return -ans;
        }
        else {
            return ans;
        }
    }

    private static String intToAbc(int v) {
        StringBuilder ans = new StringBuilder();
        boolean check = (v < 0);
        if (check) {
            v = -v;
        }
        while (v > 0) {
            ans.append((char)(v % 10 + (int)'a'));
            v /= 10;
        }
        if (check) {
            ans.append('-');
        }
        ans.reverse();
        return ans.toString();
    }

    public static void main(String[] args) {

        try {
            MyScanner in = new MyScanner(System.in);

            int[] smPref = new int[1];
            int szPref = 0;

            while (in.hasNextLine()) {
                String s = in.nextLine();
                MyScanner inNum = new MyScanner(s);

                int[] smCur = new int[1];
                int[] lineCur = new int[1];
                int sz = 0;

                while (inNum.hasNext()) {
                    int num = toInt(inNum.next());

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
                    String curSum = intToAbc(smCur[i]);
                    System.out.print(curSum);
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
