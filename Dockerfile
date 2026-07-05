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

# Application code.
COPY app ./app

# Generate the synthetic cohort at build time so the demo is self-contained,
# then pre-fit + pickle the scoring engine so a Cloud Run cold start doesn't
# pay the model-fit cost on the first request.
RUN python -m app.data_gen.build_dataset --n 400 \
    && python -m app.ml.prefit

# Cloud Run injects $PORT; Streamlit must bind it on 0.0.0.0.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "streamlit run app/frontend/main.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true"]
