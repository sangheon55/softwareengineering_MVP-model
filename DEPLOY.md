# 배포 가이드 (방식 A)

프론트엔드는 **GitHub Pages**, 백엔드(FastAPI + CLIP)는 **Hugging Face Spaces**에 올린다.

```
[브라우저] --- GitHub Pages (frontend/) --- fetch ---> Hugging Face Space (/analyze)
```

---

## 1. 백엔드 → Hugging Face Spaces

1. https://huggingface.co 가입 후 로그인.
2. **New Space** 생성
   - Space name: `pickture` (원하는 이름)
   - License: 아무거나
   - **SDK: Docker** 선택 → **Blank** 템플릿
   - Hardware: **CPU basic (무료)**
3. 이 저장소 전체를 그 Space의 git 저장소로 push 한다.
   (`Dockerfile`이 루트에 있어야 한다 — 이미 포함됨)
   ```sh
   git remote add space https://huggingface.co/spaces/<HF사용자명>/pickture
   git push space main
   ```
4. Space 페이지에서 빌드가 끝나길 기다린다(첫 빌드 + 모델 다운로드로 몇 분 소요).
5. 백엔드 주소를 확인한다: `https://<HF사용자명>-pickture.hf.space`
   - 그 주소로 접속하면 UI도 같이 뜬다(정상). API는 `.../analyze`.

## 2. 프론트엔드 → 백엔드 주소 연결

`frontend/app.js` 맨 위 `API_BASE`를 1번에서 확인한 주소로 바꾼다.

```js
const API_BASE = "https://<HF사용자명>-pickture.hf.space";
```

> 로컬에서 테스트할 때는 `""`(빈 문자열)로 두면 같은 서버를 쓴다.

변경 후 커밋:
```sh
git add frontend/app.js
git commit -m "Set backend API base to HF Space"
git push origin main
```

## 3. GitHub Pages 켜기

1. 이 저장소를 GitHub에 push (없다면 먼저 원격 저장소 생성).
2. GitHub 저장소 → **Settings → Pages**
   - **Source: GitHub Actions** 선택.
3. `main`에 push 하면 `.github/workflows/deploy-pages.yml`이 자동 실행되어
   `frontend/` 폴더를 배포한다.
4. **Actions** 탭에서 워크플로가 끝나면 페이지 주소가 나온다:
   `https://<GitHub사용자명>.github.io/<저장소명>/`

## 4. 확인

- GitHub Pages 주소로 접속 → 사진 업로드 → 분석.
- HF Space 무료 CPU는 미사용 시 잠들 수 있어, 첫 요청이 느릴 수 있다.
- 안 되면 브라우저 개발자도구(F12) Console / Network 탭에서 오류 확인.

---

## 참고

- 백엔드 코드(`backend/`, `requirements.txt`, `Dockerfile`)를 고치면
  HF Space에 다시 push 해야 반영된다 (`git push space main`).
- 프론트엔드를 고치면 GitHub에 push → Pages 워크플로가 자동 재배포한다.
- CORS는 데모용으로 모든 출처를 허용한다(`backend/main.py`). 공개 서비스라면
  `allow_origins`를 실제 Pages 주소로 좁히는 것이 좋다.
