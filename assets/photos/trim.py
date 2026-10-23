"""Erase the printed paper left under the cut-out hot dog: everything below the
underside of the frank and bun, traced by hand on the 611x605 cut-out."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
img = Image.open("cut-hotdog.webp").convert("RGBA")
mask = Image.new("L", img.size, 0)
ImageDraw.Draw(mask).polygon([(118, 605), (134, 574), (212, 514), (246, 514), (340, 480), (432, 424), (470, 605)], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(2))
px = np.array(img).astype(np.float32)
px[..., 3] *= 1 - np.array(mask, dtype=np.float32) / 255
px[..., 3] = np.where(px[..., 3] < 20, 0, px[..., 3])
out = Image.fromarray(px.astype(np.uint8))
ys, xs = np.where(px[..., 3] > 12)
out = out.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
out.save("final-hotdog.webp", "WEBP", quality=92)
print(out.size)
