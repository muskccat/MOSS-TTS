from __future__ import annotations

import html
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs" / "tool"
DEFAULT_MODEL = "OpenMOSS-Team/MOSS-TTS-Local-Transformer"
PYTHON_BIN = sys.executable
HOST = "127.0.0.1"
PORT = 7860
MAX_TEXT_LENGTH = 4000

LANGUAGE_CODES = {
    "auto": None,
    "ko": "ko",
    "korean": "ko",
    "한국어": "ko",
    "en": "en",
    "english": "en",
    "영어": "en",
}


def validate_text(text: str) -> str:
    normalized = (text or "").strip()
    if not normalized:
        raise ValueError("문장을 입력해주세요.")
    if len(normalized) > MAX_TEXT_LENGTH:
        raise ValueError(f"문장이 너무 깁니다. {MAX_TEXT_LENGTH}자 이하로 줄여주세요.")
    return normalized


def normalize_language(language: str | None) -> str | None:
    key = (language or "auto").strip().lower()
    if key not in LANGUAGE_CODES:
        raise ValueError("지원하지 않는 언어 선택입니다.")
    return LANGUAGE_CODES[key]


def make_output_stem() -> str:
    return time.strftime("moss_tts_%Y%m%d_%H%M%S")


def build_mlx_command(text: str, language: str | None, output_dir: Path, output_stem: str | None = None) -> list[str]:
    command = [
        PYTHON_BIN,
        "-m",
        "mlx_audio.tts.generate",
        "--model",
        DEFAULT_MODEL,
        "--text",
        text,
        "--output_path",
        str(output_dir),
        "--file_prefix",
        output_stem or make_output_stem(),
        "--join_audio",
        "--audio_format",
        "wav",
    ]
    lang_code = normalize_language(language)
    if lang_code is not None:
        command.extend(["--lang_code", lang_code])
    return command


def run_mlx_command(command: list[str]) -> None:
    completed = subprocess.run(
        command,
        cwd=str(BASE_DIR),
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "").strip()
        if "No Metal device available" in details:
            raise RuntimeError("MLX가 Metal GPU에 접근하지 못했습니다. 일반 터미널에서 앱을 실행해주세요.")
        raise RuntimeError(details or "오디오 생성에 실패했습니다.")


def find_newest_wav(output_dir: Path) -> Path:
    wav_files = sorted(
        output_dir.glob("*.wav"),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
    )
    if not wav_files:
        raise FileNotFoundError("생성된 wav 파일을 찾지 못했습니다.")
    return wav_files[-1]


def generate_audio_file(
    text: str,
    language: str | None,
    output_dir: Path = OUTPUT_DIR,
    output_stem: str | None = None,
) -> Path:
    safe_text = validate_text(text)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem or make_output_stem()
    target = output_dir / f"{stem}.wav"
    if target.exists():
        target.unlink()

    command = build_mlx_command(
        text=safe_text,
        language=language,
        output_dir=output_dir,
        output_stem=stem,
    )
    run_mlx_command(command)

    if target.exists():
        return target

    generated = find_newest_wav(output_dir)
    if generated != target:
        if target.exists():
            target.unlink()
        generated.replace(target)
    return target


def create_app():
    try:
        from fastapi import Body, FastAPI, HTTPException
        from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
    except ImportError as exc:
        raise RuntimeError(
            "웹 서버 패키지가 없습니다. 먼저 `uv pip install fastapi uvicorn python-multipart`를 실행해주세요."
        ) from exc

    api = FastAPI(title="MOSS-TTS Tool")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @api.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML

    @api.post("/api/generate")
    def generate(payload: dict[str, str] = Body(...)) -> JSONResponse:
        try:
            audio_path = generate_audio_file(
                payload.get("text", ""),
                payload.get("language", "auto"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return JSONResponse(
            {
                "filename": audio_path.name,
                "audio_url": f"/audio/{audio_path.name}",
                "download_url": f"/download/{audio_path.name}",
            }
        )

    @api.get("/audio/{filename}")
    def audio(filename: str) -> FileResponse:
        return serve_audio(filename, inline=True, FileResponse=FileResponse, HTTPException=HTTPException)

    @api.get("/download/{filename}")
    def download(filename: str) -> FileResponse:
        return serve_audio(filename, inline=False, FileResponse=FileResponse, HTTPException=HTTPException)

    return api


def serve_audio(filename: str, inline: bool, FileResponse: Any, HTTPException: Any):
    safe_name = Path(filename).name
    audio_path = OUTPUT_DIR / safe_name
    if not audio_path.exists() or audio_path.suffix.lower() != ".wav":
        raise HTTPException(status_code=404, detail="오디오 파일을 찾지 못했습니다.")
    disposition = "inline" if inline else f'attachment; filename="{html.escape(safe_name)}"'
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        headers={"Content-Disposition": disposition},
        filename=safe_name if not inline else None,
    )


HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MOSS-TTS</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eceef2;
      --panel: rgba(255, 255, 255, 0.82);
      --ink: #1f252e;
      --muted: #606978;
      --line: rgba(31, 37, 46, 0.14);
      --accent: #0a7cff;
      --accent-dark: #005eca;
      --danger: #b3261e;
      --shadow: 0 24px 70px rgba(30, 36, 48, 0.18);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 32px;
      background:
        linear-gradient(180deg, #f8f9fb 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    }
    .window {
      width: min(920px, 100%);
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel);
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(18px);
    }
    .titlebar {
      height: 48px;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(250, 251, 253, 0.72);
    }
    .dot { width: 12px; height: 12px; border-radius: 50%; }
    .red { background: #ff5f57; }
    .yellow { background: #febc2e; }
    .green { background: #28c840; }
    main { padding: 28px; }
    h1 {
      margin: 0 0 8px;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 0;
    }
    .sub {
      margin: 0 0 24px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
    }
    label {
      display: block;
      margin-bottom: 8px;
      color: #313844;
      font-size: 13px;
      font-weight: 650;
    }
    textarea {
      width: 100%;
      min-height: 190px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      color: var(--ink);
      background: rgba(255, 255, 255, 0.9);
      font: 16px/1.55 -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
      outline: none;
    }
    textarea:focus, select:focus {
      border-color: rgba(10, 124, 255, 0.65);
      box-shadow: 0 0 0 4px rgba(10, 124, 255, 0.12);
    }
    .controls {
      display: flex;
      gap: 12px;
      align-items: end;
      margin-top: 16px;
      flex-wrap: wrap;
    }
    .field { min-width: 180px; }
    select {
      height: 44px;
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 0 12px;
      background: white;
      color: var(--ink);
      font-size: 15px;
    }
    button, .download {
      height: 44px;
      border: 0;
      border-radius: 10px;
      padding: 0 18px;
      background: var(--accent);
      color: white;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    button:hover, .download:hover { background: var(--accent-dark); }
    button:disabled {
      opacity: 0.55;
      cursor: not-allowed;
    }
    .status {
      min-height: 24px;
      margin-top: 18px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
    }
    .status.error { color: var(--danger); }
    .player {
      display: none;
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid var(--line);
    }
    audio { width: 100%; height: 42px; }
    .actions {
      display: flex;
      justify-content: flex-end;
      margin-top: 14px;
    }
    @media (max-width: 640px) {
      body { padding: 14px; place-items: stretch; }
      main { padding: 20px; }
      .controls { display: grid; grid-template-columns: 1fr; }
      .field, button { width: 100%; }
      .actions { justify-content: stretch; }
      .download { width: 100%; }
    }
  </style>
</head>
<body>
  <section class="window" aria-label="MOSS-TTS">
    <div class="titlebar" aria-hidden="true">
      <span class="dot red"></span>
      <span class="dot yellow"></span>
      <span class="dot green"></span>
    </div>
    <main>
      <h1>MOSS-TTS</h1>
      <p class="sub">한글이나 영문 문장을 입력해서 로컬에서 음성을 생성합니다.</p>
      <form id="form">
        <label for="text">문장</label>
        <textarea id="text" maxlength="4000" placeholder="예: 안녕하세요. 맥에서 MOSS-TTS를 테스트하고 있습니다."></textarea>
        <div class="controls">
          <div class="field">
            <label for="language">언어</label>
            <select id="language">
              <option value="auto">자동</option>
              <option value="ko">한국어</option>
              <option value="en">영어</option>
            </select>
          </div>
          <button id="generate" type="submit">생성</button>
        </div>
      </form>
      <div id="status" class="status"></div>
      <section id="player" class="player">
        <audio id="audio" controls></audio>
        <div class="actions">
          <a id="download" class="download" href="#" download>WAV 저장</a>
        </div>
      </section>
    </main>
  </section>
  <script>
    const form = document.getElementById("form");
    const text = document.getElementById("text");
    const language = document.getElementById("language");
    const button = document.getElementById("generate");
    const statusBox = document.getElementById("status");
    const player = document.getElementById("player");
    const audio = document.getElementById("audio");
    const download = document.getElementById("download");

    function setStatus(message, isError = false) {
      statusBox.textContent = message;
      statusBox.classList.toggle("error", isError);
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const body = {
        text: text.value.trim(),
        language: language.value
      };
      if (!body.text) {
        setStatus("문장을 입력해주세요.", true);
        return;
      }
      button.disabled = true;
      player.style.display = "none";
      setStatus("오디오를 생성하는 중입니다. 첫 실행은 모델 로딩 때문에 시간이 걸릴 수 있습니다.");
      try {
        const response = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "오디오 생성에 실패했습니다.");
        }
        const cacheBust = `?t=${Date.now()}`;
        audio.src = data.audio_url + cacheBust;
        download.href = data.download_url;
        download.setAttribute("download", data.filename);
        player.style.display = "block";
        setStatus("생성이 끝났습니다.");
      } catch (error) {
        setStatus(error.message, true);
      } finally {
        button.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


def main() -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "웹 서버 패키지가 없습니다. 먼저 `uv pip install fastapi uvicorn python-multipart`를 실행해주세요."
        ) from exc

    uvicorn.run(create_app(), host=HOST, port=int(os.environ.get("PORT", PORT)))


if __name__ == "__main__":
    main()
