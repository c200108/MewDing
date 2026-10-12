// 把参考图标 10 号裁成 App 图标：去掉白边、外框和右下角水印，只留薄荷绿满版画面。
// 运行：java MakeIcon.java <源图> <输出目录>
// 输出：ic_launcher_foreground.png（432，自适应图标前景）、logo_cat.png（512，App 内使用）、bg_color.txt
import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.nio.file.Files;

public class MakeIcon {
    static boolean mint(int rgb) {
        int r = (rgb >> 16) & 255, g = (rgb >> 8) & 255, b = rgb & 255;
        return g > r + 18 && g > 170 && b > 150;
    }

    static BufferedImage scale(BufferedImage src, int size) {
        BufferedImage cur = src;
        int w = src.getWidth();
        while (w / 2 >= size) {
            w /= 2;
            cur = draw(cur, w);
        }
        return draw(cur, size);
    }

    static BufferedImage draw(BufferedImage src, int size) {
        BufferedImage out = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = out.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.drawImage(src, 0, 0, size, size, null);
        g.dispose();
        return out;
    }

    public static void main(String[] a) throws Exception {
        BufferedImage img = ImageIO.read(new File(a[0]));
        File out = new File(a[1]);
        out.mkdirs();
        int W = img.getWidth(), H = img.getHeight();
        // 左右边界在 30% 高度处找；上边界在正中竖线找（铃铛在下面，先碰到的是薄荷绿）；
        // 底边被小猫身体挡住，按正方形推算
        int probeY = H * 30 / 100;
        int left = 0, right = W - 1, top = 0;
        while (!mint(img.getRGB(left, probeY))) left++;
        while (!mint(img.getRGB(right, probeY))) right--;
        while (!mint(img.getRGB(W / 2, top))) top++;
        int bottom = top + (right - left);
        // 圆角半径约为边长的 17%，往里收 0.32 倍半径，四个角就全是薄荷绿
        int side = Math.min(right - left, bottom - top);
        int inset = (int) (side * 0.17 * 0.32) + 6;
        int x0 = left + inset, y0 = top + inset;
        int cs = side - inset * 2;
        System.out.printf("mint box %d,%d - %d,%d  crop %d,%d size %d%n", left, top, right, bottom, x0, y0, cs);
        BufferedImage crop = img.getSubimage(x0, y0, cs, cs);

        ImageIO.write(scale(crop, 512), "png", new File(out, "logo_cat.png"));
        ImageIO.write(scale(crop, 1024), "png", new File(out, "萌叮图标_1024.png"));

        // 自适应图标：108dp 画布里可见的是中间 72dp，前景把画面放在中间 2/3（略放大一点盖住接缝）
        int full = 432, inner = 296;
        BufferedImage fg = new BufferedImage(full, full, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = fg.createGraphics();
        g.drawImage(scale(crop, inner), (full - inner) / 2, (full - inner) / 2, null);
        g.dispose();
        ImageIO.write(fg, "png", new File(out, "ic_launcher_foreground.png"));

        int c = crop.getRGB(cs / 2, 4);
        String hex = String.format("#%06X", c & 0xFFFFFF);
        Files.writeString(new File(out, "bg_color.txt").toPath(), hex);
        System.out.println("bg " + hex);
    }
}
