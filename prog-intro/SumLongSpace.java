 public class SumLongSpace {
    
    public static void main(String[] args) {
        
        long ans = 0;

        for (String arg : args) {
            int argSize = arg.length();

            int l = 0, r = 0;
            while (l < argSize) {
                char c = arg.charAt(l);
                if (Character.getType(c) != Character.SPACE_SEPARATOR) {
                    r = l + 1;
                    while (r < argSize && Character.getType(arg.charAt(r)) != Character.SPACE_SEPARATOR) {
                        r++;
                    }
                    long number = Long.parseLong(arg.substring(l, r));
                    ans += number;
                    l = r;
                    continue;
                }
                l++;
            }
        }
        
        System.out.println(ans);
    }
}
