"""Flask web server for the Sobel edge detection service.

Images are processed entirely in memory; nothing is written to disk.
"""

import os
from pathlib import PurePath
from urllib.parse import quote

from flask import Flask, Response, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from edge_detector import sobel_edge_detect

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "gif", "webp", "tiff", "tif"}
MAX_UPLOAD_MB = 10

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def _error(message: str, status: int):
    return jsonify({"error": message}), status


def _extension(filename: str) -> str:
    return PurePath(filename).suffix.lower().lstrip(".")


@app.get("/")
def index():
    return render_template(
        "index.html",
        max_mb=MAX_UPLOAD_MB,
        accept=",".join("." + e for e in sorted(ALLOWED_EXTENSIONS)),
    )


@app.get("/healthz")
def healthz():
    return Response("ok", status=200, mimetype="text/plain")


@app.post("/api/edge")
def edge():
    file = request.files.get("image")
    if file is None or not file.filename:
        return _error("이미지 파일이 없습니다. 'image' 필드로 파일을 업로드해 주세요.", 400)

    ext = _extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return _error(f"지원하지 않는 파일 형식입니다. 허용 형식: {allowed}", 400)

    data = file.read()
    if not data:
        return _error("빈 파일입니다.", 400)

    try:
        png_bytes = sobel_edge_detect(data)
    except ValueError:
        return _error("이미지를 해석할 수 없습니다. 올바른 이미지 파일인지 확인해 주세요.", 400)

    original_stem = PurePath(file.filename).stem
    ascii_name = f"{secure_filename(original_stem) or 'image'}_sobel.png"
    # filename* (RFC 5987) keeps non-ASCII names such as Korean; filename is the ASCII fallback.
    utf8_name = quote(f"{original_stem.replace('/', '_').replace(chr(92), '_')}_sobel.png")

    resp = Response(png_bytes, status=200, mimetype="image/png")
    resp.headers["Content-Disposition"] = (
        f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}"
    )
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.errorhandler(RequestEntityTooLarge)
def too_large(_e):
    return _error(f"파일이 너무 큽니다. 최대 {MAX_UPLOAD_MB}MB까지 업로드할 수 있습니다.", 413)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
