# TwinDock as ONE always-on container: the built frontend, /api and /ws from a single FastAPI process.
# The world lives in that process's memory, so it runs exactly one worker (docs/deploy_diagnosis.md).
#
#   docker build -t twindock .
#   docker run --rm -p 7860:7860 twindock            # http://localhost:7860
#   docker run --rm -p 7860:7860 -e MQTT_URL=mqtts://user:pass@host:8883 twindock   # let a real board join

# ---- 1. frontend: vite build (imports the JSON schemas from ../shared)
FROM node:22-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY shared /src/shared
COPY frontend ./
RUN npm run build

# ---- 2. backend: slim Python serving everything
FROM python:3.12-slim
# TZ is the site's time zone: solar output, shifts and tariffs follow the simulated local time (override with -e TZ=...).
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PORT=7860 \
    TZ=Asia/Kolkata \
    TWINDOCK_MQTT=0 \
    TWINDOCK_SIM=auto
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r backend/requirements.txt
# Same layout as the repo, so every path in the code works unchanged.
COPY shared shared
COPY hardware hardware
COPY tools/site_sim.py tools/sim_models.py tools/
COPY backend/twindock backend/twindock
COPY backend/world backend/world
COPY backend/rules backend/rules
COPY --from=frontend /src/frontend/dist frontend/dist
# Hugging Face Spaces runs the container as uid 1000; nothing here writes to disk except the historian (R6).
RUN useradd -m -u 1000 twindock && chown -R twindock /app
USER twindock
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import os,urllib.request;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"7860\")}/api/health',timeout=4)"
# One worker, always: two would be two separate worlds.
CMD ["sh", "-c", "exec uvicorn twindock.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-7860} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
