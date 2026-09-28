"""Sobel edge detection using only numpy and Pillow.

Public API:
    sobel_edge_detect(image_bytes: bytes) -> bytes

CLI:
    python edge_detector.py input.jpg output.png
"""

import io
import sys

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

# Images whose longest side exceeds this are downscaled (aspect ratio kept)
# before processing, to bound memory and CPU use on the server.
MAX_SIDE = 4000

# 3x3 Sobel kernels (horizontal and vertical gradients).
SOBEL_X = np.array([[-1, 0, 1],
                    [-2, 0, 2],
                    [-1, 0, 1]], dtype=np.float32)
SOBEL_Y = SOBEL_X.T


def _load_grayscale(image_bytes: bytes) -> Image.Image:
    """Decode bytes into an 8-bit grayscale PIL image.

    Applies EXIF orientation, flattens any transparency onto a white
    background (RGBA, LA, palette-with-transparency), and downscales so the
    longest side is at most MAX_SIDE pixels.
    """
    if not image_bytes:
        raise ValueError("Empty input: no image data provided.")
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except (UnidentifiedImageError, OSError, SyntaxError,
            Image.DecompressionBombError) as exc:
        raise ValueError(f"Could not decode image data: {exc}") from exc

    img = ImageOps.exif_transpose(img)

    # Downscale huge images proportionally (thumbnail never upscales).
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)

    # Flatten transparency onto white so transparent areas are uniform.
    if img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info:
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        img = Image.alpha_composite(background, rgba)

    return img.convert("L")


def _sobel_magnitude(gray: np.ndarray) -> np.ndarray:
    """Return the Sobel gradient magnitude of a 2D float array.

    Vectorized: the image is edge-padded by one pixel, then each of the nine
    kernel taps is applied as a shifted slice of the padded array.
    """
    h, w = gray.shape
    padded = np.pad(gray, 1, mode="edge")
    gx = np.zeros((h, w), dtype=np.float32)
    gy = np.zeros((h, w), dtype=np.float32)
    for dy in range(3):
        for dx in range(3):
            window = padded[dy:dy + h, dx:dx + w]
            if SOBEL_X[dy, dx]:
                gx += SOBEL_X[dy, dx] * window
            if SOBEL_Y[dy, dx]:
                gy += SOBEL_Y[dy, dx] * window
    return np.hypot(gx, gy)


def sobel_edge_detect(image_bytes: bytes) -> bytes:
    """Take raw uploaded image bytes (JPEG/PNG/etc.), return the Sobel edge
    magnitude image encoded as PNG bytes.

    The input is converted to grayscale (after EXIF orientation and alpha
    flattening). The magnitude sqrt(Gx^2 + Gy^2) is normalized to 0-255 and
    returned as an 8-bit grayscale PNG with the same width/height as the
    (orientation-corrected) input.

    Note: if the longest side exceeds MAX_SIDE (4000 px), the image is first
    downscaled proportionally, so the output will have that reduced size.

    Raises:
        ValueError: if the bytes are empty or not a decodable image.
    """
    gray_img = _load_grayscale(image_bytes)
    gray = np.asarray(gray_img, dtype=np.float32)

    magnitude = _sobel_magnitude(gray)
    peak = magnitude.max()
    if peak > 0:
        magnitude *= 255.0 / peak
    edges = np.clip(np.rint(magnitude), 0, 255).astype(np.uint8)

    out = io.BytesIO()
    Image.fromarray(edges).save(out, format="PNG", optimize=False)
    return out.getvalue()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python edge_detector.py input_image output.png",
              file=sys.stderr)
        return 2
    in_path, out_path = argv[1], argv[2]
    with open(in_path, "rb") as f:
        data = f.read()
    try:
        png = sobel_edge_detect(data)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    with open(out_path, "wb") as f:
        f.write(png)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
