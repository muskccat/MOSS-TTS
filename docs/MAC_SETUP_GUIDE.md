# MOSS-TTS 맥 설치 가이드

이 문서는 맥에서 한글 또는 영문 텍스트를 입력하면 MOSS-TTS로 음성을 생성하는 로컬 툴을 만들기 위한 사전 설치 가이드입니다.

## 0. 먼저 알아둘 점

- MOSS-TTS는 TTS, 즉 텍스트를 음성으로 바꾸는 모델입니다. 따라서 최종 출력은 보통 `.wav` 같은 음성 파일이거나 재생 가능한 오디오입니다.
- 공식 MOSS-TTS 설치 예시는 현재 CUDA 기반 PyTorch 환경을 중심으로 되어 있습니다. 맥, 특히 Apple Silicon 맥에서는 그대로 따라 하면 설치가 꼬일 수 있습니다.
- 맥에서는 우선 Apple Silicon에 맞춰진 `mlx-audio` 경로부터 테스트하는 것을 권장합니다.
- 한글 입력은 모델과 실행 백엔드에 따라 품질 차이가 있을 수 있습니다. 그래서 실제 툴을 만들기 전에 짧은 한글/영문 문장으로 먼저 음성 생성이 되는지 확인하는 것이 좋습니다.
- 가능하면 Apple Silicon 맥을 권장합니다. 메모리는 16GB도 시도는 가능하지만, 큰 모델은 빡빡할 수 있고 24GB 이상이면 더 안정적입니다.

## 1. 권장 진행 방향

권장 순서는 다음과 같습니다.

1. Homebrew로 기본 시스템 도구를 설치합니다.
2. Python 3.12 가상환경을 새로 만듭니다.
3. Apple Silicon 친화적인 `mlx-audio`를 먼저 설치합니다.
4. 터미널에서 영문과 한글 TTS 생성 테스트를 합니다.
5. 테스트가 성공하면 그 명령/API를 감싸는 로컬 UI 툴을 만듭니다.

이 순서를 추천하는 이유는 다음과 같습니다.

- 공식 MOSS-TTS 저장소는 최근 업데이트에서 MLX 지원을 언급하고 있습니다.
- 공식 PyTorch 런타임 의존성은 CUDA 휠을 고정하고 있어 맥에 바로 맞지 않습니다.
- `mlx-audio`는 명령어와 Python API를 제공하므로 이후 로컬 앱으로 감싸기 쉽습니다.

## 2. 사전 도구 설치

### Homebrew 설치

Homebrew가 없다면 먼저 설치합니다.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

그 다음 필요한 도구를 설치합니다.

```bash
brew update
brew install git ffmpeg python@3.12 uv
```

설치가 잘 되었는지 확인합니다.

```bash
git --version
ffmpeg -version
python3.12 --version
uv --version
```

## 3. 프로젝트용 Python 환경 만들기

원하는 위치에서 새 프로젝트 폴더를 만듭니다.

```bash
mkdir -p ~/Documents/moss-tts-tool
cd ~/Documents/moss-tts-tool
uv venv --python 3.12 .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

터미널 앞쪽에 `(.venv)` 같은 표시가 보이면 가상환경이 활성화된 상태입니다.

## 4. MLX-Audio로 첫 TTS 테스트

먼저 `mlx-audio`를 설치합니다.

```bash
uv pip install mlx-audio
```

영문 테스트를 먼저 실행합니다.

```bash
mlx_audio.tts.generate \
  --model OpenMOSS-Team/MOSS-TTS-Local-Transformer \
  --text "Hello, this is a first MOSS TTS test on Mac." \
  --output_path ./outputs \
  --join_audio
```

그 다음 한글 테스트를 실행합니다.

```bash
mlx_audio.tts.generate \
  --model OpenMOSS-Team/MOSS-TTS-Local-Transformer \
  --text "안녕하세요. 맥에서 모스 티티에스를 테스트하고 있습니다." \
  --output_path ./outputs \
  --join_audio
```

성공하면 `outputs` 폴더 아래에 `.wav` 파일이 생성됩니다.

만약 위 모델 이름으로 실행되지 않는다면, `mlx-audio`에서 제공하는 MOSS-TTS 계열의 더 작은 모델이나 양자화 모델을 먼저 시도하는 것이 좋습니다.

## 5. 선택 사항: 공식 MOSS-TTS 저장소 받기

공식 예제와 데모 스크립트를 참고하기 위해 저장소를 받아둘 수 있습니다.

```bash
git clone https://github.com/OpenMOSS/MOSS-TTS.git
cd MOSS-TTS
```

단, 맥에서는 아래 공식 CUDA 설치 명령을 그대로 실행하지 않는 것을 권장합니다.

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime]"
```

이 명령은 CUDA용 PyTorch 휠을 설치하는 흐름입니다. 맥에서는 먼저 MLX 경로를 테스트하고, 필요할 때만 CPU/MPS 호환 PyTorch 경로를 따로 잡는 편이 안전합니다.

## 6. 선택 사항: 공식 저장소를 맥에서 실험하기

이 단계는 MLX 경로가 잘 되는지 확인한 뒤에만 시도하는 것을 추천합니다.

```bash
cd ~/Documents/moss-tts-tool
git clone https://github.com/OpenMOSS/MOSS-TTS.git
cd MOSS-TTS
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e .
uv pip install torch torchaudio torchcodec transformers accelerate
```

이 방식은 맥에서 느리거나 일부 패키지 때문에 실패할 수 있습니다. 특히 `torchcodec`, 모델 크기, 백엔드 지원 여부에 영향을 받습니다.

## 7. 설치 후 확인해주면 좋은 것

사전 셋업이 끝나면 아래 내용을 알려주세요.

- 맥 칩 종류: Apple Silicon인지 Intel인지
- 메모리 용량: 16GB, 24GB, 32GB 등
- `ffmpeg -version` 실행 여부
- `uv --version` 실행 여부
- 영문 테스트 음성이 생성되었는지
- 한글 테스트 음성이 생성되었는지
- `outputs` 폴더에 생성된 파일 이름

이 정보를 알면 다음 단계에서 툴 구현 방식을 더 정확히 잡을 수 있습니다.

## 8. 다음 단계에서 만들 툴 형태

TTS 명령이 정상 동작하면 첫 버전은 작고 실용적으로 만드는 것이 좋습니다.

- 로컬 웹 UI 또는 작은 데스크톱 래퍼
- 한글/영문 텍스트 입력창
- 언어 선택: 자동, 한국어, 영어
- 생성 버튼
- 생성된 음성 바로 재생
- `.wav` 파일 저장
- 최근 생성 기록

처음부터 음성 복제, 스트리밍, 앱 패키징까지 넣기보다는 한글/영문 품질을 먼저 확인한 뒤 기능을 넓히는 편이 좋습니다.

## 참고 링크

- MOSS-TTS 저장소: https://github.com/OpenMOSS/MOSS-TTS
- MOSS-TTS 공식 설치 안내: https://github.com/OpenMOSS/MOSS-TTS#environment-setup
- MOSS-TTS llama.cpp / PyTorch-free 안내: https://github.com/OpenMOSS/MOSS-TTS#llamacpp-backend-torch-free-inference
- MLX-Audio 저장소: https://github.com/Blaizzy/mlx-audio
