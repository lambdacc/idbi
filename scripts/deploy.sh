#!/usr/bin/env bash
#
# CreditPulse — manual Cloud Run deploy (IDBI Innovate 2026).
#
# One human-run script. NOT wired to CI/CD — nothing here fires on a git push.
# You run it by hand when you want to ship: `./scripts/deploy.sh`.
#
# It is idempotent: safe to re-run. Enabling an already-enabled API, re-creating
# an existing Artifact Registry repo, or redeploying are all no-op-or-update, so
# running it twice just ships the latest code again.
#
# Mirrors internal/deployment-runbook.md step-for-step; see that doc for the "why"
# behind each Cloud Run flag.
#
# Usage:
#   ./scripts/deploy.sh              # full flow: preflight → APIs → repo → build → deploy → smoke
#   ./scripts/deploy.sh build        # build & push the image only
#   ./scripts/deploy.sh deploy       # deploy the current :latest image only (no rebuild)
#   ./scripts/deploy.sh smoke        # curl the live URL
#   ./scripts/deploy.sh url          # print the live service URL
#   ./scripts/deploy.sh warm         # min-instances=1 (avoid cold start before a judging window)
#   ./scripts/deploy.sh cold         # min-instances=0 (back to scale-to-zero after)
#   ./scripts/deploy.sh logs         # tail recent logs
#   ./scripts/deploy.sh teardown     # delete the service + image repo
#
# Override any default inline, e.g.:
#   REGION=asia-south2 ./scripts/deploy.sh
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

  # Warn (don't fail) if billing looks disabled — build/deploy will fail without it.
  if gcloud beta billing projects describe "$PROJECT_ID" >/dev/null 2>&1; then
    local enabled
    enabled="$(gcloud beta billing projects describe "$PROJECT_ID" --format='value(billingEnabled)' 2>/dev/null || echo '')"
    if [ "$enabled" != "True" ]; then
      warn "Billing appears DISABLED on '$PROJECT_ID' — Cloud Build & Cloud Run need it. Link a billing account before continuing."
    else
      ok "Billing enabled"
    fi
  else
    warn "Could not verify billing status (needs the billing API / permission). Continuing anyway."
  fi
}

# ---- APIs (idempotent) -----------------------------------------------------
enable_apis() {
  step "Enabling required APIs (idempotent)"
  gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com
  ok "run, artifactregistry, cloudbuild enabled"
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

# ---- Build (Cloud Build — no local Docker needed) --------------------------
build() {
  step "Building image via Cloud Build → ${IMAGE}:latest"
  warn "This builds from the current working tree (not a git ref). Commit/clean first if you want a reproducible ref."
  gcloud builds submit --tag "${IMAGE}:latest" .
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
    warn "Got HTTP $code from $u (a first-hit cold start can take a few seconds — retry, or check: $0 logs)"
  fi
  echo "  ${DIM}Manual pass: open $u in incognito and run one assessment end-to-end (see internal/deployment-runbook.md §3).${RST}"
}

# ---- Warm / cold (judging-window switches) ---------------------------------
warm_up() {
  step "Setting min-instances=1 (no cold starts during the judging window)"
  gcloud run services update "$SERVICE" --region "$REGION" --min-instances 1
  ok "Warm. Remember to run '$0 cold' afterwards to stop paying for an idle instance."
}
cool_down() {
  step "Setting min-instances=0 (scale to zero)"
  gcloud run services update "$SERVICE" --region "$REGION" --min-instances 0
  ok "Back to scale-to-zero."
}

# ---- Logs ------------------------------------------------------------------
logs() {
  step "Recent logs for '$SERVICE'"
  gcloud run services logs read "$SERVICE" --region "$REGION" --limit 100
}

# ---- Teardown --------------------------------------------------------------
teardown() {
  step "Teardown"
  warn "This deletes the Cloud Run service AND the image repo for project '$PROJECT_ID'."
  read -r -p "  Type the project id ('$PROJECT_ID') to confirm: " confirm
  [ "$confirm" = "$PROJECT_ID" ] || die "Aborted (confirmation did not match)."
  gcloud run services delete "$SERVICE" --region "$REGION" --quiet || true
  gcloud artifacts repositories delete "$REPO" --location "$REGION" --quiet || true
  ok "Service and repo deleted. (Delete the whole project separately if it was demo-only.)"
}

# ---- Full flow -------------------------------------------------------------
all() {
  preflight
  enable_apis
  ensure_repo
  build
  deploy
  smoke
  echo "${BOLD}${GREEN}Done.${RST} Deploy link above. To avoid cold starts before judging: ${BOLD}$0 warm${RST}"
}

# ---- Dispatch --------------------------------------------------------------
case "${1:-all}" in
  all)       all ;;
  preflight) preflight ;;
  apis)      preflight; enable_apis ;;
  repo)      preflight; ensure_repo ;;
  build)     preflight; enable_apis; ensure_repo; build ;;
  deploy)    preflight; deploy ;;
  smoke)     smoke ;;
  url)       url ;;
  warm)      warm_up ;;
  cold)      cool_down ;;
  logs)      logs ;;
  teardown)  teardown ;;
  -h|--help|help)
    sed -n '2,27p' "$0" | sed 's/^# \{0,1\}//' ;;
  *)
    die "Unknown command '$1'. Run '$0 --help'." ;;
esac
