"""CLIP ViT-L/14 로딩 및 임베딩/점수 산출.

미학 점수는 CLIP에 전용 헤드가 없으므로 제로샷 텍스트 프롬프트로 근사한다.
정확도를 더 높이려면 LAION aesthetic predictor(CLIP 임베딩 위 MLP)로 교체하면
되지만, 별도 가중치 파일이 필요하므로 MVP에서는 채택하지 않는다.
"""

import threading

import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

MODEL_ID = "openai/clip-vit-large-patch14"
_BATCH_SIZE = 8

# 미학 평가용 프롬프트. 앞쪽 _N_POSITIVE개가 긍정, 나머지가 부정.
_AES_POSITIVE = [
    "a high quality, sharp, well-composed photograph",
    "a professional, beautifully lit photo",
]
_AES_NEGATIVE = [
    "a blurry, out-of-focus, low quality photo",
    "a poorly composed, badly lit snapshot",
]
_AES_PROMPTS = _AES_POSITIVE + _AES_NEGATIVE
_N_POSITIVE = len(_AES_POSITIVE)

_model = None
_processor = None
_lock = threading.Lock()


def get_model():
    """모델/프로세서를 최초 1회만 로드해 캐시한다 (스레드 안전)."""
    global _model, _processor
    if _model is None:
        with _lock:
            if _model is None:
                proc = CLIPProcessor.from_pretrained(MODEL_ID)
                model = CLIPModel.from_pretrained(MODEL_ID)
                model.eval()
                _processor, _model = proc, model
    return _model, _processor


def _l2_normalize(arr):
    norms = np.linalg.norm(arr, axis=-1, keepdims=True)
    return arr / np.clip(norms, 1e-8, None)


@torch.no_grad()
def embed_images(pil_images):
    """이미지 리스트를 L2 정규화된 임베딩 행렬로 변환."""
    model, processor = get_model()
    chunks = []
    for i in range(0, len(pil_images), _BATCH_SIZE):
        batch = pil_images[i:i + _BATCH_SIZE]
        inputs = processor(images=batch, return_tensors="pt")
        feats = model.get_image_features(**inputs)
        chunks.append(feats.cpu().numpy())
    return _l2_normalize(np.concatenate(chunks, axis=0))


@torch.no_grad()
def embed_text(text):
    """텍스트 한 줄을 L2 정규화된 임베딩 벡터로 변환."""
    model, processor = get_model()
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    feats = model.get_text_features(**inputs)
    return _l2_normalize(feats.cpu().numpy())[0]


@torch.no_grad()
def aesthetic_scores(pil_images):
    """이미지별 미학 점수(긍정 프롬프트 확률 합, 0~1)를 반환."""
    model, processor = get_model()
    scores = []
    for i in range(0, len(pil_images), _BATCH_SIZE):
        batch = pil_images[i:i + _BATCH_SIZE]
        inputs = processor(
            text=_AES_PROMPTS, images=batch,
            return_tensors="pt", padding=True,
        )
        logits = model(**inputs).logits_per_image
        probs = logits.softmax(dim=-1)
        positive = probs[:, :_N_POSITIVE].sum(dim=-1)
        scores.extend(positive.cpu().numpy().tolist())
    return scores
