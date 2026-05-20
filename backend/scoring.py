"""점수 정규화, 최종 가중 합산, 하드 필터링, 코멘트 생성."""

import numpy as np

_TEXT_BLEND_WEIGHT = 0.3  # 분위기 텍스트가 Vibe 타깃에 섞이는 비중


def _normalize(vec):
    return vec / max(float(np.linalg.norm(vec)), 1e-8)


def vibe_target(ref_embeds, text_embed=None):
    """기준 피드 임베딩의 centroid에 (선택적으로) 분위기 텍스트를 블렌딩."""
    centroid = _normalize(ref_embeds.mean(axis=0))
    if text_embed is None:
        return centroid
    blended = (1 - _TEXT_BLEND_WEIGHT) * centroid + _TEXT_BLEND_WEIGHT * text_embed
    return _normalize(blended)


def minmax_to_10(values):
    """배치 내 min-max 정규화로 0~10 스케일 변환. 편차가 없으면 모두 5.0."""
    arr = np.asarray(values, dtype=float)
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo < 1e-6:
        return [5.0] * len(arr)
    return (10.0 * (arr - lo) / (hi - lo)).tolist()


def _make_comment(aes, vibe):
    if aes >= 7:
        a = "화질·구도가 뛰어남"
    elif aes >= 4:
        a = "화질·구도는 무난함"
    else:
        a = "화질·구도가 다소 아쉬움"
    if vibe >= 7:
        v = "기존 피드와 매우 잘 어울림"
    elif vibe >= 4:
        v = "기존 피드와 어느 정도 어울림"
    else:
        v = "기존 피드 톤과는 다소 이질적"
    return f"{a} · {v}"


def rank_candidates(candidates, vibe_raw, aes_raw, w_vibe, threshold):
    """후보별 표시 점수를 산출하고 하드 필터 후 최종 점수로 정렬한다.

    candidates: [{"name", "thumbnail"}, ...]
    vibe_raw: 코사인 유사도 원점수, aes_raw: 미학 확률(0~1) 원점수
    반환: (ranked, filtered) — 각각 점수/순위가 채워진 dict 리스트
    """
    vibe_display = minmax_to_10(vibe_raw)
    w_aes = 1.0 - w_vibe
    results = []
    for i, c in enumerate(candidates):
        sv = round(vibe_display[i], 2)
        sa = round(min(max(aes_raw[i] * 10.0, 0.0), 10.0), 2)
        results.append({
            "name": c["name"],
            "thumbnail": c["thumbnail"],
            "vibe": sv,
            "aesthetic": sa,
            "final": round(w_vibe * sv + w_aes * sa, 2),
            "comment": _make_comment(sa, sv),
        })

    ranked = [r for r in results if r["aesthetic"] >= threshold]
    filtered = [r for r in results if r["aesthetic"] < threshold]
    ranked.sort(key=lambda r: r["final"], reverse=True)
    filtered.sort(key=lambda r: r["aesthetic"], reverse=True)
    for idx, r in enumerate(ranked):
        r["rank"] = idx + 1
    return ranked, filtered
