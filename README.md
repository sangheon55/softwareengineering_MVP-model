---
title: pick!ture
emoji: 📸
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# pick!ture — AI 기반 SNS 사진 자동 선별 서비스 (MVP)

CLIP ViT-L/14 모델로 SNS에 올릴 후보 사진을 분석해, **기존 피드 스타일과의
조화도(Vibe)** 와 **사진의 미학 품질(Aesthetic)** 을 점수화하고 최적의 사진을
랭킹해 주는 웹 서비스입니다.

> 소프트웨어공학 팀 프로젝트 — MVP 단계 구현체

## 🌐 라이브 데모

- **웹 서비스**: https://sangheon55.github.io/softwareengineering_MVP-model/
- **백엔드 (Hugging Face Space)**: https://huggingface.co/spaces/heon55/pickture

> 프론트엔드는 GitHub Pages, 백엔드(FastAPI + CLIP)는 Hugging Face Spaces에
> 배포되어 있습니다. 배포 방법은 [DEPLOY.md](DEPLOY.md)를 참고하세요.
> 아래 "설치 / 실행"은 로컬 개발용 안내입니다.

---

## 핵심 기능

| 기능 | 설명 |
|------|------|
| 기준 피드 학습 | 내 기존 게시물 5~10장으로 톤앤매너 기준을 구축 |
| 후보 분석 | 최대 30장의 후보 사진을 일괄 분석 |
| 미학 점수 (Saes) | CLIP 제로샷 프롬프트로 화질·구도·조명 품질 평가 |
| Vibe 점수 (Svibe) | 기준 피드와의 코사인 유사도로 스타일 일관성 측정 |
| 최종 랭킹 | `Final = 0.8 × Svibe + 0.2 × Saes` (가중치 조절 가능) |
| 하드 필터 | 미학 점수가 임계값 미만인 사진을 랭킹에서 제외 |
| 피드 미리보기 | 선택한 사진을 기존 피드에 배치한 모습을 시뮬레이션 |

## 기술 스택

- **백엔드**: Python 3.12, FastAPI, Uvicorn
- **AI 모델**: OpenAI CLIP `ViT-L/14` (HuggingFace `transformers`, PyTorch CPU)
- **프런트엔드**: 순수 HTML / CSS / JavaScript (빌드 과정 없음)

---

## 🧠 AI 작동 방식

pick!ture는 OpenAI의 **CLIP (ViT-L/14)** 모델 하나만으로 두 가지 점수를 산출합니다.
CLIP은 이미지와 텍스트를 같은 의미 공간의 벡터(임베딩)로 변환하는 모델입니다.

### 1. 임베딩 추출

모든 이미지를 CLIP으로 768차원 벡터로 변환하고 L2 정규화합니다. 정규화하면
두 벡터의 내적이 곧 **코사인 유사도**(스타일이 얼마나 비슷한지)가 됩니다.

### 2. Vibe 점수 — 기존 피드와의 조화도

1. 기준 피드 이미지들의 임베딩을 평균내어 **"내 피드 스타일 벡터"**(centroid)를 만듭니다.
2. 분위기 텍스트를 입력하면, 그 텍스트의 임베딩을 30% 비중으로 블렌딩합니다.
3. 각 후보 이미지와 이 스타일 벡터의 **코사인 유사도**를 계산합니다.
4. 후보들 사이에서 min-max 정규화해 0~10점으로 환산합니다.

### 3. Aesthetic 점수 — 사진의 미학 품질

CLIP에는 화질 평가 전용 출력이 없어, **제로샷 텍스트 프롬프트**로 근사합니다.

- 긍정 프롬프트: `"a high quality, sharp, well-composed photograph"` 등 2개
- 부정 프롬프트: `"a blurry, out-of-focus, low quality photo"` 등 2개

각 이미지가 이 4개 프롬프트 중 어디에 더 가까운지를 softmax 확률로 구한 뒤,
**긍정 프롬프트 확률의 합(0~1)** 을 미학 점수로 삼아 0~10점으로 환산합니다.

### 4. 최종 랭킹

```
Final = w_vibe × Svibe + w_aes × Saes   (기본 0.8 / 0.2, 슬라이더로 조절)
```

1. 미학 점수가 **하드 필터 임계값** 미만인 사진은 랭킹에서 제외합니다.
2. 통과한 사진을 최종 점수 내림차순으로 정렬해 순위를 매깁니다.

> CLIP 추론만 사용하므로 별도 학습이나 GPU가 필요 없습니다. 미학 점수는
> 제로샷 근사 방식이라, 추후 LAION aesthetic predictor로 고도화할 수 있습니다.

---

## 설치 (Windows)

> Python 3.10 이상 필요. 없다면 [python.org](https://www.python.org/downloads/)
> 또는 `winget install Python.Python.3.12` 로 설치하세요.

```bat
:: 1. 저장소 클론
git clone https://github.com/sangheon55/softwareengineering_MVP-model.git
cd softwareengineering_MVP-model

:: 2. 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

:: 3. PyTorch (CPU 빌드) 먼저 설치 — CUDA 대용량 휠 방지
pip install torch --index-url https://download.pytorch.org/whl/cpu

:: 4. 나머지 의존성 설치
pip install -r requirements.txt
```

## 실행

```bat
run.bat
```

또는 직접:

```bat
venv\Scripts\activate
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

브라우저에서 **http://localhost:8000** 접속.

### 최초 실행 시 주의

- 첫 실행 때 CLIP ViT-L/14 모델(**약 1.7GB**)을 자동 다운로드합니다.
  네트워크 속도에 따라 수 분 걸릴 수 있으며, `~/.cache/huggingface` 에
  캐시되어 이후엔 즉시 로드됩니다. (모델 파일은 git에 포함되지 않음)
- CPU 추론 기준 이미지당 약 0.3~1초. 후보 30장이면 30~60초 소요될 수 있습니다.

---

## 사용법

1. **기준 피드** — 본인의 기존 게시물 사진 5~10장 업로드
2. **후보 사진** — 분석할 사진 최대 30장 업로드
3. **분위기 텍스트** (선택) — 예: `따뜻하고 차분한 감성`
4. 가중치 / 하드 필터 임계값 슬라이더 조절 후 **분석하기**
5. 점수순 랭킹 대시보드 확인 → 카드 클릭 시 피드 미리보기

## 프로젝트 구조

```
softwareengineering_MVP-model/
├─ backend/
│  ├─ main.py          FastAPI 앱: UI 서빙 + /analyze 파이프라인
│  ├─ clip_engine.py   CLIP 모델 로드, 이미지/텍스트 임베딩, 미학 점수
│  └─ scoring.py       점수 정규화, 최종 가중합, 하드 필터, 코멘트
├─ frontend/
│  ├─ index.html       업로드 폼 + 결과 대시보드 + 미리보기 모달
│  ├─ style.css
│  └─ app.js           /analyze 호출 및 렌더링
├─ requirements.txt
├─ run.bat             Windows 실행 스크립트
└─ *.pdf               요구사항 분석 / 과제 기획 문서
```

---

## MVP 범위 및 한계

이번 구현은 **MVP 단계**로, 다음은 의도적으로 제외했습니다:

- 지인 투표·공유 기능 (F4.1)
- 회원 가입 / 인증, 데이터베이스 영속화
- 성능 최적화 (ONNX / TensorRT, GPU 추론) — 요구사항의 "5초 이내"는 향후 목표
- 미학 점수는 CLIP 제로샷 프롬프트 방식 → 추후 LAION aesthetic predictor로 고도화 가능

## 팀원

김종빈 · 김민규 · 이규현 · 이상헌 · 이종화 · 이지민
