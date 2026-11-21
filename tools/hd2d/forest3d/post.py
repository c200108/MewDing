# 后期：泛光（亮部高斯模糊叠加）+ 暖色调色 + 暗角，模拟参考视频的 HD-2D 画面
import sys, numpy as np
from PIL import Image, ImageFilter
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(np.float32) / 255
lum = a @ [.299, .587, .114]
bright = np.clip((lum - .62) / .38, 0, 1)[..., None] * a
b = Image.fromarray((bright * 255).astype(np.uint8))
bl = sum(np.asarray(b.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255 * w for r, w in ((6, .5), (18, .45), (40, .35)))
o = a + bl * .55
o = o * [1.04, 1.0, .93] + [.01, .005, 0]                     # 暖一点
o = (o - .5) * 1.06 + .5                                      # 轻微提对比
h, w = lum.shape; yy, xx = np.mgrid[0:h, 0:w]
v = 1 - .28 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) ** 1.4
o *= v[..., None]
Image.fromarray((np.clip(o, 0, 1) * 255).astype(np.uint8)).save(dst, quality=93)
