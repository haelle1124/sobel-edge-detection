(function () {
  "use strict";

  var ALLOWED = ["jpg", "jpeg", "png", "bmp", "gif", "webp", "tiff", "tif"];
  var MAX_BYTES = (window.MAX_MB || 10) * 1024 * 1024;

  var dropzone = document.getElementById("dropzone");
  var input = document.getElementById("file-input");
  var fileNameEl = document.getElementById("file-name");
  var runBtn = document.getElementById("run-btn");
  var downloadBtn = document.getElementById("download-btn");
  var errorEl = document.getElementById("error");
  var results = document.getElementById("results");
  var originalImg = document.getElementById("original-img");
  var resultFig = document.getElementById("result-fig");
  var resultImg = document.getElementById("result-img");

  var currentFile = null;
  var originalUrl = null;
  var resultUrl = null;

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.hidden = false;
  }
  function clearError() {
    errorEl.textContent = "";
    errorEl.hidden = true;
  }
  function revoke(url) { if (url) URL.revokeObjectURL(url); }

  function resetResult() {
    revoke(resultUrl);
    resultUrl = null;
    resultImg.removeAttribute("src");
    resultFig.hidden = true;
    downloadBtn.hidden = true;
    downloadBtn.removeAttribute("href");
  }

  function extOf(name) {
    var i = name.lastIndexOf(".");
    return i >= 0 ? name.slice(i + 1).toLowerCase() : "";
  }

  function setFile(file) {
    clearError();
    resetResult();
    if (!file) return;
    if (ALLOWED.indexOf(extOf(file.name)) === -1) {
      showError("지원하지 않는 파일 형식입니다. (JPG, PNG, BMP, GIF, WEBP, TIFF)");
      return;
    }
    if (file.size > MAX_BYTES) {
      showError("파일이 너무 큽니다. 최대 " + (window.MAX_MB || 10) + "MB까지 업로드할 수 있습니다.");
      return;
    }
    currentFile = file;
    fileNameEl.textContent = file.name;
    revoke(originalUrl);
    originalUrl = URL.createObjectURL(file);
    originalImg.src = originalUrl;
    results.hidden = false;
    runBtn.disabled = false;
  }

  function filenameFromDisposition(header, fallback) {
    if (!header) return fallback;
    var star = /filename\*\s*=\s*(?:UTF-8'')?([^;]+)/i.exec(header);
    if (star) {
      try { return decodeURIComponent(star[1].trim().replace(/^"|"$/g, "")); } catch (e) { /* ignore */ }
    }
    var plain = /filename\s*=\s*"?([^";]+)"?/i.exec(header);
    return plain ? plain[1].trim() : fallback;
  }

  function setLoading(on) {
    runBtn.disabled = on;
    runBtn.classList.toggle("loading", on);
    runBtn.querySelector(".label").textContent = on ? "처리 중..." : "엣지 검출";
  }

  async function run() {
    if (!currentFile) return;
    clearError();
    resetResult();
    setLoading(true);
    try {
      var form = new FormData();
      form.append("image", currentFile, currentFile.name);
      var res = await fetch("/api/edge", { method: "POST", body: form });
      if (!res.ok) {
        var msg = "처리 중 오류가 발생했습니다. (HTTP " + res.status + ")";
        try {
          var data = await res.json();
          if (data && data.error) msg = data.error;
        } catch (e) { /* non-JSON error body */ }
        throw new Error(msg);
      }
      var blob = await res.blob();
      var name = filenameFromDisposition(res.headers.get("Content-Disposition"), "result_sobel.png");
      resultUrl = URL.createObjectURL(blob);
      resultImg.src = resultUrl;
      resultFig.hidden = false;
      downloadBtn.href = resultUrl;
      downloadBtn.download = name;
      downloadBtn.hidden = false;
    } catch (err) {
      showError(err && err.message ? err.message : "네트워크 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  input.addEventListener("change", function () {
    setFile(input.files && input.files[0]);
  });

  dropzone.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
  });

  ["dragenter", "dragover"].forEach(function (t) {
    dropzone.addEventListener(t, function (e) {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });
  ["dragleave", "drop"].forEach(function (t) {
    dropzone.addEventListener(t, function (e) {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });
  dropzone.addEventListener("drop", function (e) {
    var f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) setFile(f);
  });
  // Prevent the browser from opening files dropped outside the zone.
  window.addEventListener("dragover", function (e) { e.preventDefault(); });
  window.addEventListener("drop", function (e) { e.preventDefault(); });

  runBtn.addEventListener("click", run);
})();
