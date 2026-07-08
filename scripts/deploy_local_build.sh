#!/usr/bin/env bash
#
# CreditPulse — LOCAL-Docker deploy to Cloud Run (IDBI Innovate 2026).
#
# The alternative to scripts/deploy.sh. Instead of Cloud Build, this builds the
# image on THIS machine and pushes it with YOUR OWN gcloud credentials. Use it
# when Cloud Build's push fails with:
#
#     denied: Permission 'artifactregistry.repositories.uploadArtifacts' denied
#
# That error is the Cloud Build service account (…-compute@developer…) lacking
# Artifact Registry Writer. A local `docker push` authenticates as your user
# account (the one that created the repo), so it sidesteps that permission wall
# with no IAM changes — and skips the Cloud Build round-trip entirely. Cost is a
# wash either way (Cloud Build gives 120 free build-min/day); this is about
# getting past the permission error, not saving money.
#
# Requires a running local Docker daemon. Same config/flags as deploy.sh, so the
# resulting Cloud Run service is identical.
#
# Usage:
#   ./scripts/deploy_local_build.sh          # full flow: preflight → APIs → repo → build → push → deploy → smoke
#   ./scripts/deploy_local_build.sh build    # build & push the image locally only (no deploy)
#   ./scripts/deploy_local_build.sh deploy   # deploy the current :latest image only (no rebuild)
#   ./scripts/deploy_local_build.sh smoke    # curl the live URL
#   ./scripts/deploy_local_build.sh url      # print the live service URL
#
# For warm / cold (judging-window min-instances), logs, and teardown, use the
# Cloud Build script: ./scripts/deploy.sh warm | cold | logs | teardown
#
# Override any default inline, e.g.:
#   REGION=asia-south2 ./scripts/deploy_local_build.sh
#
# Fallback if a LOCAL push also denies uploadArtifacts (your user account lacks
# the role too), grant it and retry — or grant the Cloud Build SA and use
# deploy.sh instead:
#   gcloud projects add-iam-policy-binding idbi-hackathon \
#     --member=serviceAccount:624680413525-compute@developer.gserviceaccount.com \
#     --role=roles/artifactregistry.writer
#   gcloud projects add-iam-policy-binding idbi-hackathon \
#     --member=serviceAccount:624680413525-compute@developer.gserviceaccount.com \
#     --role=roles/logging.logWriter
#
set -euo pipefail

# ---- Configuration (override via environment) ------------------------------
PROJECT_ID="${PROJECT_ID:-idbi-hackathon}"
REGION="${REGION:-asia-south1}"          # Mumbai — closest to the audience
SERVICE="${SERVICE:-creditpulse}"
REPO="${REPO:-creditpulse}"              # Artifact Registry repo name
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}"

# ---- Pretty logging --------------------------------------------------------
if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; RST=$'\033[0m'
else
  BOLD=''; DIM=''; GREEN=''; YELLOW=''; RED=''; RST=''
fi
step() { echo "${BOLD}==>${RST} $*"; }
ok()   { echo "${GREEN}  ✓${RST} $*"; }
warn() { echo "${YELLOW}  ! ${RST}$*"; }
die()  { echo "${RED}✗ $*${RST}" >&2; exit 1; }

# ---- Preflight -------------------------------------------------------------
preflight() {
  step "Preflight"
  command -v gcloud >/dev/null 2>&1 || die "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"

  # Local Docker is what makes this script different from deploy.sh.
  command -v docker >/dev/null 2>&1 || die "Docker not found locally. Use Cloud Build instead:  ./scripts/deploy.sh build"
  docker info >/dev/null 2>&1 || die "Docker daemon not reachable. Start Docker and retry (or use ./scripts/deploy.sh build)."
  ok "Docker reachable ($(docker --version 2>/dev/null | sed 's/,.*//'))"

  # Are we authenticated?
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    die "No active gcloud login. Run:  gcloud auth login"
  fi
  ok "gcloud authenticated as $(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -1)"

  # Does the project exist and can we see it?
  if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
    die "Project '$PROJECT_ID' not found or no access. Create it (with billing enabled) first:
       gcloud projects create $PROJECT_ID
       # then link a billing account in the Console: Billing → link project"
  fi
  ok "Project '$PROJECT_ID' reachable"

  gcloud config set project "$PROJECT_ID" >/dev/null 2>&1
  gcloud config set run/region "$REGION" >/dev/null 2>&1
  ok "Config set: project=$PROJECT_ID  region=$REGION"

  # Warn (don't fail) if billing looks disabled — deploy will fail without it.
  if gcloud beta billing projects describe "$PROJECT_ID" >/dev/null 2>&1; then
    local enabled
    enabled="$(gcloud beta billing projects describe "$PROJECT_ID" --format='value(billingEnabled)' 2>/dev/null || echo '')"
    if [ "$enabled" != "True" ]; then
      warn "Billing appears DISABLED on '$PROJECT_ID' — Cloud Run needs it. Link a billing account before continuing."
    else
      ok "Billing enabled"
    fi
  else
    warn "Could not verify billing status (needs the billing API / permission). Continuing anyway."
  fi
}

# ---- APIs (idempotent) -----------------------------------------------------
# The local-build path does NOT use Cloud Build, so only Run + Artifact Registry.
enable_apis() {
  step "Enabling required APIs (idempotent)"
  gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com
  ok "run, artifactregistry enabled"
}

# ---- Artifact Registry repo (idempotent) -----------------------------------
ensure_repo() {
  step "Ensuring Artifact Registry repo '$REPO' in $REGION"
  if gcloud artifacts repositories describe "$REPO" --location="$REGION" >/dev/null 2>&1; then
    ok "Repo '$REPO' already exists"
  else
    gcloud artifacts repositories create "$REPO" \
      --repository-format=docker \
      --location="$REGION" \
      --description="CreditPulse demo images"
    ok "Repo '$REPO' created"
  fi
}

# ---- Build locally + push as the current user ------------------------------
build_local() {
  step "Configuring Docker auth for ${REGION}-docker.pkg.dev (idempotent)"
  gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
  ok "Credential helper installed in ~/.docker/config.json"

  step "Building image locally → ${IMAGE}:latest  (--platform linux/amd64)"
  warn "Builds from the working tree; .dockerignore trims the context. Commit/clean first for a reproducible ref."
  # --platform linux/amd64 guarantees a Cloud Run-compatible image even if this
  # host is arm64. The Dockerfile regenerates synthetic data + pre-fits models at
  # build time, so the result matches the Cloud Build image.
  docker build --platform linux/amd64 -t "${IMAGE}:latest" .
  ok "Image built"

  step "Pushing ${IMAGE}:latest  (as $(gcloud config get-value account 2>/dev/null))"
  docker push "${IMAGE}:latest"
  ok "Image pushed: ${IMAGE}:latest"
}

# ---- Deploy ----------------------------------------------------------------
deploy() {
  step "Deploying '$SERVICE' to Cloud Run ($REGION)"
  gcloud run deploy "$SERVICE" \
    --image "${IMAGE}:latest" \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --cpu 1 --memory 2Gi \
    --min-instances 0 --max-instances 1 \
    --concurrency 40 \
    --timeout 3600 \
    --session-affinity
  local url; url="$(service_url)"
  ok "Deployed."
  echo
  echo "  ${BOLD}Live URL:${RST} ${GREEN}${url}${RST}"
  echo "  ${DIM}(this is the deploy link for the submission — same URL serves Overview + /track03 /track04 /track05)${RST}"
  echo
}

service_url() {
  gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)' 2>/dev/null
}

url() {
  local u; u="$(service_url)"
  [ -n "$u" ] || die "Service '$SERVICE' not found in $REGION. Deploy it first."
  echo "$u"
}

# ---- Smoke test ------------------------------------------------------------
smoke() {
  step "Smoke test"
  local u; u="$(service_url)"
  [ -n "$u" ] || die "Service '$SERVICE' not found in $REGION. Deploy it first."
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 60 "$u" || echo 000)"
  if [ "$code" = "200" ]; then
    ok "HTTP 200 from $u"
  else
    warn "Got HTTP $code from $u (a first-hit cold start can take a few seconds — retry, or check: ./scripts/deploy.sh logs)"
  fi
  echo "  ${DIM}Manual pass: open $u in incognito and run one assessment end-to-end (see internal/deployment-runbook.md §3).${RST}"
}

# ---- Full flow -------------------------------------------------------------
all() {
  preflight
  enable_apis
  ensure_repo
  build_local
  deploy
  smoke
  echo "${BOLD}${GREEN}Done (local build).${RST} Deploy link above. To avoid cold starts before judging: ${BOLD}./scripts/deploy.sh warm${RST}"
}

# ---- Dispatch --------------------------------------------------------------
case "${1:-all}" in
  all)       all ;;
  preflight) preflight ;;
  apis)      preflight; enable_apis ;;
  repo)      preflight; ensure_repo ;;
  build)     preflight; enable_apis; ensure_repo; build_local ;;
  deploy)    preflight; deploy ;;
  smoke)     smoke ;;
  url)       url ;;
  -h|--help|help)
    sed -n '2,42p' "$0" | sed 's/^# \{0,1\}//' ;;
  *)
    die "Unknown command '$1'. Run '$0 --help'." ;;
esac
