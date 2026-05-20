# Hugging Face Spaces (Docker SDK)용 이미지 — pick!ture 백엔드
FROM python:3.11-slim

# HF Spaces 권장: 비루트 사용자로 실행
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# 의존성 먼저 설치(레이어 캐시 활용). torch는 CPU 휠로 따로 설치.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY --chown=user . .

# HF Spaces Docker 컨테이너는 7860 포트를 노출해야 한다.
EXPOSE 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
