# Deployment Runbook — CreditPulse on Google Cloud Run

**Status:** Operational runbook · **Date:** 02 Jul 2026 · **Owner:** Lambdac
**Reads with:** [`implementation-plan.md`](implementation-plan.md) §8 (deployment architecture and its rationale)

Step-by-step instructions to take the repo from a clean checkout to a public
Cloud Run URL, plus the demo-day switches, smoke test, rollback, and teardown.
Written to be followed top-to-bottom by anyone with Owner/Editor access to a
GCP project; no prior state assumed.

> Flag names and defaults below were written against Cloud Run as of mid-2026 —
> if a `gcloud` command rejects a flag, check `gcloud run deploy --help` first;
> the concept (session affinity, min instances, request timeout) is what matters.

---

## 0. One-time prerequisites

1. **Install the gcloud CLI** (https://cloud.google.com/sdk/docs/install) and log in:
   ```bash
   gcloud auth login
   ```
2. **Create (or pick) a project** with billing enabled, then set the shell context
   used by every command below:
   ```bash
   export PROJECT_ID="creditpulse-demo"        # <-- your project id
   export REGION="asia-south1"                 # Mumbai — closest to the audience
   export SERVICE="creditpulse"
   export REPO="creditpulse"                   # Artifact Registry repo name
   export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}"

   gcloud config set project "$PROJECT_ID"
   gcloud config set run/region "$REGION"
   ```
3. **Enable the required APIs** (one-time per project):
   ```bash
   gcloud services enable run.googleapis.com \
                          artifactregistry.googleapis.com \
                          cloudbuild.googleapis.com
   ```
4. **Create the Artifact Registry Docker repo** (one-time):
   ```bash
   gcloud artifacts repositories create "$REPO" \
     --repository-format=docker --location="$REGION" \
     --description="CreditPulse demo images"
   ```

## 1. Build the image

Two equivalent paths — pick one.

**Option A — Cloud Build (no local Docker needed, recommended):**
```bash
gcloud builds submit --tag "${IMAGE}:latest" .
```

**Option B — local Docker:**
```bash
gcloud auth configure-docker "${REGION}-docker.pkg.dev"
docker build -t "${IMAGE}:latest" .
docker push "${IMAGE}:latest"
```

The Dockerfile generates the synthetic cohort **and pre-fits the scoring engine at
build time** (`app.data_gen.build_dataset` + `app.ml.prefit`), so the container
serves its first request without a model-fit delay. `.dockerignore` keeps
`docs/`, `internal/`, and local data out of the build context.

Sanity-check locally before deploying (optional but cheap):
```bash
docker run --rm -e PORT=8080 -p 8080:8080 "${IMAGE}:latest"
# open http://localhost:8080 — pick an archetype, Run Assessment end-to-end
```

## 2. Deploy

```bash
gcloud run deploy "$SERVICE" \
  --image "${IMAGE}:latest" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 2 --memory 2Gi \
  --min-instances 0 --max-instances 3 \
  --concurrency 40 \
  --timeout 3600 \
  --session-affinity
```

Why each non-default flag (rationale in `implementation-plan.md` §8):

| Flag | Why |
|---|---|
| `--allow-unauthenticated` | Public demo link — the submission requirement. No secrets or real data are in the app (synthetic only). |
| `--cpu 2 --memory 2Gi` | Comfortable headroom for Streamlit + LightGBM + Plotly; scale up only if the live demo shows latency. |
| `--min-instances 0` | Scale-to-zero between demo sessions — the lowest-cost default. |
| `--max-instances 3` | Caps the bill; a demo never needs more. |
| `--concurrency 40` | Streamlit sessions are stateful; a modest cap keeps one instance from juggling too many live WebSocket sessions. |
| `--timeout 3600` | Streamlit's UI runs over a persistent WebSocket; Cloud Run closes connections at the request timeout, so set it to the maximum (60 min) to avoid mid-demo disconnects. |
| `--session-affinity` | Routes a returning client to the same instance, so a session's state survives the WebSocket reconnect dance. |

The command prints the service URL (`https://<service>-<hash>-<region>.a.run.app`).
That URL is the deploy link for the submission.

## 3. Smoke test (after every deploy)

1. Open the service URL in a fresh browser/incognito window.
2. Pick **Sunrise Textiles** → **Run Assessment** with *Staged reveal* ON → the
   9-stage pipeline plays through to the Health Card without errors.
3. Repeat with *Staged reveal* OFF (Instant mode) → lands directly on the card.
4. Open the **Financial Health Card**, **Explainability**, and **Architecture**
   pages once each.
5. Cold-start check: wait ~20 minutes (instance scaled to zero), reload, and
   confirm the first page paints within a few seconds (the pre-fit engine means
   no model-fitting delay on top of the container start).

The full expected on-screen content per step is in [`demo-script.md`](demo-script.md).

## 4. Demo-day / judging-window switches

Cold starts are cheap to avoid when it matters. Just before a judging window or
live demo:
```bash
gcloud run services update "$SERVICE" --region "$REGION" --min-instances 1
```
Revert afterwards to go back to scale-to-zero cost:
```bash
gcloud run services update "$SERVICE" --region "$REGION" --min-instances 0
```

## 5. Updating the deployment

Rebuild and redeploy — Cloud Run keeps every previous revision:
```bash
gcloud builds submit --tag "${IMAGE}:latest" .
gcloud run deploy "$SERVICE" --image "${IMAGE}:latest" --region "$REGION"
```
Redeploys reuse the service's existing flags; only pass flags you want to change.

**Rollback** (instant, no rebuild) — shift traffic back to a known-good revision:
```bash
gcloud run revisions list --service "$SERVICE" --region "$REGION"
gcloud run services update-traffic "$SERVICE" --region "$REGION" \
  --to-revisions <GOOD_REVISION>=100
```

## 6. Observability

- **Logs**: `gcloud run services logs read "$SERVICE" --region "$REGION" --limit 100`
  (or the Cloud Run console → Logs tab). Streamlit tracebacks land here.
- **Metrics**: Cloud Run console → Metrics tab — watch instance count, request
  latency, and container-start latency around demo sessions.

## 7. Cost expectations

With `min-instances 0`, cost accrues only while requests are being served —
idle time is free. A 2-vCPU/2-GiB instance running continuously (`min-instances 1`)
is on the order of a few USD per day, so the judging-window switch (§4) is the
only period worth paying for. Artifact Registry storage for a handful of image
versions is cents. Set a **budget alert** on the project as a backstop:
Console → Billing → Budgets & alerts.

## 8. Teardown (after the hackathon)

```bash
gcloud run services delete "$SERVICE" --region "$REGION"
gcloud artifacts repositories delete "$REPO" --location "$REGION"
```
Or delete the whole project if it was created only for this demo.

## 9. Known limitations / future hardening

- **No CI→CD wiring yet**: CI builds the image but does not deploy. When wanted,
  add a deploy job using Workload Identity Federation (keyless GitHub→GCP auth) —
  avoid long-lived JSON service-account keys in repo secrets.
- **Single region, no custom domain**: fine for a demo; a bank pilot would front
  this with a load balancer, custom domain, and Cloud Armor.
- **Session state is in-memory per instance**: session affinity makes this fine at
  demo scale; production would externalize state.
