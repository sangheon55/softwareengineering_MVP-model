"use strict";

const $ = (id) => document.getElementById(id);

const refInput = $("reference-input");
const candInput = $("candidate-input");
const vibeSlider = $("vibe-slider");
const thresholdSlider = $("threshold-slider");

// 피드 미리보기에 쓰려고 기준 피드 이미지의 object URL을 보관한다.
let refPreviewUrls = [];

function renderPreview(files, container, isReference) {
  container.innerHTML = "";
  if (isReference) {
    refPreviewUrls.forEach((u) => URL.revokeObjectURL(u));
    refPreviewUrls = [];
  }
  Array.from(files).forEach((file) => {
    if (!file.type.startsWith("image/")) return;
    const url = URL.createObjectURL(file);
    if (isReference) refPreviewUrls.push(url);
    const img = document.createElement("img");
    img.src = url;
    container.appendChild(img);
  });
}

refInput.addEventListener("change", () =>
  renderPreview(refInput.files, $("reference-preview"), true));
candInput.addEventListener("change", () =>
  renderPreview(candInput.files, $("candidate-preview"), false));

vibeSlider.addEventListener("input", () => {
  const v = parseFloat(vibeSlider.value);
  $("weight-label").textContent = `${v.toFixed(2)} / ${(1 - v).toFixed(2)}`;
});
thresholdSlider.addEventListener("input", () => {
  $("threshold-label").textContent = parseFloat(thresholdSlider.value).toFixed(1);
});

function scoreClass(score) {
  if (score >= 7) return "s-good";
  if (score >= 4) return "s-mid";
  return "s-bad";
}

function metricBar(label, score) {
  return `
    <div class="metric">
      <div class="metric-head"><span>${label}</span><span>${score.toFixed(1)}</span></div>
      <div class="bar"><span class="${scoreClass(score)}" style="width:${score * 10}%"></span></div>
    </div>`;
}

function resultCard(item, opts) {
  const card = document.createElement("div");
  card.className = "result-card" + (opts.dimmed ? " dimmed" : "");
  const badge = opts.dimmed
    ? `<span class="rank-badge" style="background:#9ca3af">제외</span>`
    : `<span class="rank-badge${item.rank === 1 ? " top" : ""}">${item.rank}위</span>`;
  card.innerHTML = `
    <div class="photo">${badge}<img src="${item.thumbnail}" alt="${item.name}" /></div>
    <div class="card-body">
      <div class="final-score">
        <span class="num">${item.final.toFixed(1)}</span><span class="unit">/ 10 최종점수</span>
      </div>
      ${metricBar("피드 조화도", item.vibe)}
      ${metricBar("미학 점수", item.aesthetic)}
      <div class="comment">${item.comment}</div>
    </div>`;
  card.addEventListener("click", () => openFeedPreview(item.thumbnail));
  return card;
}

function openFeedPreview(thumbnail) {
  const grid = $("feed-grid");
  grid.innerHTML = "";
  const picked = document.createElement("img");
  picked.src = thumbnail;
  picked.className = "picked";
  grid.appendChild(picked);
  refPreviewUrls.forEach((url) => {
    const img = document.createElement("img");
    img.src = url;
    grid.appendChild(img);
  });
  $("preview-modal").hidden = false;
}

$("modal-close").addEventListener("click", () => ($("preview-modal").hidden = true));
$("preview-modal").addEventListener("click", (e) => {
  if (e.target.id === "preview-modal") $("preview-modal").hidden = true;
});

function setStatus(html, isError) {
  const el = $("status");
  el.hidden = false;
  el.className = "status" + (isError ? " error" : "");
  el.innerHTML = html;
}

function renderResults(data) {
  $("results").hidden = false;
  $("results-meta").textContent =
    `기준 피드 ${data.ref_count}장 · 가중치 조화도 ${data.w_vibe} / 미학 ${data.w_aes}` +
    ` · 임계값 ${data.threshold}` +
    (data.skipped ? ` · 손상/비이미지 ${data.skipped}장 제외` : "");

  const rankedList = $("ranked-list");
  rankedList.innerHTML = "";
  if (data.ranked.length === 0) {
    rankedList.innerHTML =
      `<p class="hint">임계값을 통과한 사진이 없어요. 임계값을 낮춰 다시 시도해 보세요.</p>`;
  } else {
    data.ranked.forEach((item) =>
      rankedList.appendChild(resultCard(item, { dimmed: false })));
  }

  const filteredBlock = $("filtered-block");
  const filteredList = $("filtered-list");
  filteredList.innerHTML = "";
  if (data.filtered.length > 0) {
    filteredBlock.hidden = false;
    data.filtered.forEach((item) =>
      filteredList.appendChild(resultCard(item, { dimmed: true })));
  } else {
    filteredBlock.hidden = true;
  }
  $("results").scrollIntoView({ behavior: "smooth" });
}

$("analyze-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (refInput.files.length === 0) {
    setStatus("기준 피드 사진을 1장 이상 올려주세요.", true);
    return;
  }
  if (candInput.files.length === 0) {
    setStatus("후보 사진을 1장 이상 올려주세요.", true);
    return;
  }

  const form = new FormData();
  Array.from(refInput.files).forEach((f) => form.append("reference", f));
  Array.from(candInput.files).forEach((f) => form.append("candidates", f));
  form.append("mood", $("mood-input").value);
  form.append("w_vibe", vibeSlider.value);
  form.append("threshold", thresholdSlider.value);

  const btn = $("analyze-btn");
  btn.disabled = true;
  $("results").hidden = true;
  setStatus(
    `<span class="spinner"></span>AI가 사진을 분석 중이에요... ` +
    `(CPU 추론이라 사진 수에 따라 수십 초 걸릴 수 있어요)`,
    false);

  try {
    const res = await fetch("/analyze", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) {
      setStatus(data.error || "분석 중 오류가 발생했어요.", true);
      return;
    }
    $("status").hidden = true;
    renderResults(data);
  } catch (err) {
    setStatus("서버에 연결하지 못했어요: " + err.message, true);
  } finally {
    btn.disabled = false;
  }
});
