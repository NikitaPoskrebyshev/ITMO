import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.io.ByteArrayInputStream;

public class MyScanner {
    private final BufferedReader reader;
    private final String lineSep;

    public MyScanner(String input) throws IOException {
        byte[] bytes = input.getBytes(StandardCharsets.UTF_8);
        InputStream in = new ByteArrayInputStream(bytes);
        reader = new BufferedReader(new InputStreamReader(in));
        lineSep = System.lineSeparator();
    }

    public MyScanner(InputStream input) throws IOException {
        reader = new BufferedReader(new InputStreamReader(input));
        lineSep = System.lineSeparator();
    }

    public String nextLine() throws IOException {
        return reader.readLine();
    }

    public String next() throws IOException {
        StringBuilder s = new StringBuilder();
        int r = reader.read();
        String R = String.valueOf((char)r);
        while (r >= 0 && R.equals(" ")) {
            r = reader.read();
            R = String.valueOf((char)r);
        }
        while (r >= 0 && !R.equals(" ") && !R.equals(lineSep)) {
            s.append(R);
            r = reader.read();
            R = String.valueOf((char)r);
        }
        return s.toString();
    }

    public int nextInt() throws IOException {
        return Integer.parseInt(next());
    }

    public boolean hasNext() throws IOException {
        reader.mark(10);
        int r = reader.read();
        String R = String.valueOf((char)r);
        while (r >= 0) {
            if (!R.equals(" ") && !R.equals(lineSep)) {
                reader.reset();
                return true;
            }
            r = reader.read();
            R = String.valueOf((char)r);
        }
        reader.reset();
        return false;
    }

    public boolean hasNextLine() throws IOException {
        reader.mark(5);
        int r = reader.read();
        reader.reset();
        return r >= 0;
    }

    public void close() throws IOException {
        reader.close();
    }
}
