# pick!ture — AI 기반 SNS 사진 자동 선별 서비스 (MVP)

CLIP ViT-L/14 모델로 SNS에 올릴 후보 사진을 분석해, **기존 피드 스타일과의
조화도(Vibe)** 와 **사진의 미학 품질(Aesthetic)** 을 점수화하고 최적의 사진을
랭킹해 주는 웹 서비스입니다.

> 소프트웨어공학 팀 프로젝트 — MVP 단계 구현체
> (외부 서버·DB 없이 전부 localhost에서 동작)

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
