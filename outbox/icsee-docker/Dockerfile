# icsee-docker: DVRIP-native HTTP API for ICSee/XM cameras (x86_64).
# No FunSDK is used or needed (see ARCH-BLOCKER-REPORT.md): the service
# speaks DVRIP directly (TCP 34567) with Python + FFmpeg.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY tests ./tests

# Unit tests gate the build: G.711 codec + DVRIP framing must pass.
RUN python -m pytest tests/ -q

RUN useradd -m -u 10001 icsee && chown -R icsee:icsee /app
USER icsee

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=4)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
