"""pick!ture MVP — FastAPI 앱: 정적 UI 서빙 + /analyze 분석 파이프라인."""

import base64
import io
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from backend import clip_engine, scoring

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
MAX_CANDIDATES = 30
THUMBNAIL_SIZE = (320, 320)

app = FastAPI(title="pick!ture MVP")


@app.middleware("http")
async def _no_cache(request, call_next):
    """MVP 개발 중 정적 파일이 캐시되어 옛 화면이 보이는 문제를 막는다."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.on_event("startup")
def _warm_model():
    """첫 요청 지연을 줄이기 위해 서버 기동 시 모델을 미리 로드한다."""
    try:
        clip_engine.get_model()
        print("[pick!ture] CLIP model loaded")
    except Exception as exc:  # 다운로드 실패 등 — 첫 요청에서 재시도된다
        print(f"[pick!ture] model preload warning: {exc}")


def _load_image(upload: UploadFile):
    """업로드 파일을 RGB PIL 이미지로 변환. 실패하면 None."""
    try:
        img = Image.open(io.BytesIO(upload.file.read()))
        img.load()
        return img.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def _thumbnail_data_uri(img: Image.Image):
    thumb = img.copy()
    thumb.thumbnail(THUMBNAIL_SIZE)
    buf = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/analyze")
async def analyze(
    reference: list[UploadFile] = File(default=[]),
    candidates: list[UploadFile] = File(default=[]),
    mood: str = Form(default=""),
    w_vibe: float = Form(default=0.8),
    threshold: float = Form(default=3.5),
):
    ref_images = [im for im in (_load_image(f) for f in reference) if im is not None]
    if not ref_images:
        return JSONResponse(
            {"error": "기준 피드 이미지를 1장 이상 업로드하세요."}, status_code=400)

    cand_pairs = []
    for f in candidates:
        img = _load_image(f)
        if img is not None:
            cand_pairs.append((f.filename or f"image_{len(cand_pairs)}", img))
    skipped = len(candidates) - len(cand_pairs)
    cand_pairs = cand_pairs[:MAX_CANDIDATES]
    if not cand_pairs:
        return JSONResponse(
            {"error": "분석 가능한 후보 이미지가 없습니다."}, status_code=400)

    w_vibe = min(max(w_vibe, 0.0), 1.0)
    threshold = min(max(threshold, 0.0), 10.0)

    ref_embeds = clip_engine.embed_images(ref_images)
    text_embed = clip_engine.embed_text(mood) if mood.strip() else None
    target = scoring.vibe_target(ref_embeds, text_embed)

    cand_images = [img for _, img in cand_pairs]
    cand_embeds = clip_engine.embed_images(cand_images)
    vibe_raw = (cand_embeds @ target).tolist()
    aes_raw = clip_engine.aesthetic_scores(cand_images)

    meta = [
        {"name": name, "thumbnail": _thumbnail_data_uri(img)}
        for name, img in cand_pairs
    ]
    ranked, filtered = scoring.rank_candidates(
        meta, vibe_raw, aes_raw, w_vibe, threshold)

    return JSONResponse({
        "ranked": ranked,
        "filtered": filtered,
        "w_vibe": round(w_vibe, 2),
        "w_aes": round(1.0 - w_vibe, 2),
        "threshold": round(threshold, 2),
        "ref_count": len(ref_images),
        "skipped": skipped,
    })


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
