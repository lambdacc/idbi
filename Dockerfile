# CreditPulse — single-stage image for Cloud Run (implementation-plan.md §8).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# LightGBM needs the OpenMP runtime (libgomp1) on slim Debian images.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit theme + browser config. MUST be copied: it pins base="light" so
# widget text renders dark-on-light regardless of the viewer's OS dark-mode
# preference. Without it, Streamlit follows prefers-color-scheme and dark-theme
# text lands invisibly on custom.css's light panels. Streamlit reads it from
# $CWD/.streamlit/config.toml, and the app is launched from WORKDIR /srv.
COPY .streamlit ./.streamlit

# Application code.
COPY app ./app

# Generate the synthetic cohort(s) at build time so the demo is self-contained,
# then pre-fit + pickle every engine so a Cloud Run cold start doesn't pay the
# model-fit cost on the first request. Track data-gen is folder-guarded so the
# image builds whether or not the track CSVs are committed (an installed track
# without data is rebuilt here; a deleted track is skipped) — this keeps the
# deploy decoupled from the track-CSV commit-vs-gitignore choice.
RUN python -m app.data_gen.build_dataset --n 400 \
    && if [ -d app/tracks/t04_early_warning ]; then python -m app.tracks.t04_early_warning.data_gen.build; fi \
    && if [ -d app/tracks/t05_fraud_intelligence ]; then python -m app.tracks.t05_fraud_intelligence.data_gen.build; fi \
    && python -m app.ml.prefit

# Cloud Run injects $PORT; Streamlit must bind it on 0.0.0.0.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "streamlit run app/frontend/main.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true"]
