# MOSS-TTS Mac Tool

맥에서 한글 또는 영문 문장을 입력하면 MOSS-TTS 계열 모델로 음성을 생성하는 간단한 로컬 웹 툴입니다.

현재 버전은 Apple Silicon 맥에서 `mlx-audio`를 사용하는 흐름을 기준으로 정리되어 있습니다. 공식 OpenMOSS 저장소를 직접 수정하지 않고, 로컬 웹 UI가 `mlx_audio.tts.generate` 명령을 호출해 `.wav` 파일을 생성합니다.

## 포함된 내용

- `app.py`: 한글/영문 텍스트 입력, 언어 선택, 음성 생성, 재생, WAV 다운로드를 제공하는 로컬 웹 앱
- `test_app.py`: 입력 검증, `mlx-audio` 명령 생성, 파일 처리, API 오류 응답 테스트
- `docs/MAC_SETUP_GUIDE.md`: 맥 설치 및 사전 셋업 가이드
- `requirements.txt`: 앱 실행에 필요한 Python 패키지

## 빠른 실행

```bash
brew install git ffmpeg python@3.12 uv

mkdir -p ~/Documents/moss-tts-tool
cd ~/Documents/moss-tts-tool
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
python app.py
```

브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:7860
```

생성된 오디오는 기본적으로 `outputs/tool` 폴더에 저장됩니다.

## 모델

기본 모델은 다음으로 설정되어 있습니다.

```text
OpenMOSS-Team/MOSS-TTS-Local-Transformer
```

필요하면 `app.py`의 `DEFAULT_MODEL` 값을 다른 `mlx-audio` 호환 MOSS-TTS 모델로 바꿀 수 있습니다.

## 테스트

```bash
python -m unittest test_app.py
```

Codex 같은 샌드박스 환경에서는 MLX가 Metal GPU에 접근하지 못할 수 있습니다. 실제 음성 생성 검증은 일반 macOS 터미널에서 실행하는 것을 권장합니다.
