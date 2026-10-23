"""Cut the subject out of a photo and save a trimmed transparent WebP.
usage: python cutout.py <src> <dst.webp> [model] [max_side]"""
import sys

import numpy as np
from PIL import Image
from rembg import new_session, remove

src, dst = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "isnet-general-use"
max_side = int(sys.argv[4]) if len(sys.argv) > 4 else 1600

img = Image.open(src).convert("RGB")
out = remove(img, session=new_session(model), alpha_matting=True,
             alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=15,
             alpha_matting_erode_size=6)
alpha = np.array(out)[..., 3]
ys, xs = np.where(alpha > 12)
pad = 12
box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, out.width), min(ys.max() + pad, out.height))
out = out.crop(box)
if max(out.size) > max_side:
    k = max_side / max(out.size)
    out = out.resize((round(out.width * k), round(out.height * k)), Image.LANCZOS)
out.save(dst, "WEBP", quality=90)
print(dst, out.size, "from", img.size, "box", box)
