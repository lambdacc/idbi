#!/usr/bin/env bash
#
# CreditPulse — Artifact Registry image cleanup (IDBI Innovate 2026).
#
# Run this AFTER a deploy. Every build pushes `creditpulse:latest`; pushing a new
# :latest re-points the tag and leaves the PREVIOUS image UNTAGGED (dangling) in
# Artifact Registry — not deleted. Each is a ~1-2 GB image, so they pile up one
# per redeploy and quietly accrue storage cost. This prunes those dangling images.
#
# SAFETY: it only ever deletes UNTAGGED images, and it additionally protects the
# exact image digest the currently-serving Cloud Run revision runs — so it can
# never break the live service, even if run between a push and a deploy. The
# tagged `:latest` is protected for free (it has a tag).
#
# It does NOT touch Cloud Run itself. Old revisions sit at 0 instances (scale to
# zero) and cost nothing; there is no old "copy" running to delete.
#
# Usage:
#   ./scripts/cleanup_images.sh            # prune all untagged images (keeps active + :latest)
#   ./scripts/cleanup_images.sh dry        # show what WOULD be deleted, delete nothing
#   ./scripts/cleanup_images.sh list       # list every image version with tags, mark the active one
#
# Override any default inline, e.g.:
#   REGION=asia-south2 ./scripts/cleanup_images.sh dry
#
set -euo pipefail

# ---- Configuration (override via environment) — mirrors deploy_local_build.sh
PROJECT_ID="${PROJECT_ID:-idbi-hackathon}"
REGION="${REGION:-asia-south1}"
SERVICE="${SERVICE:-creditpulse}"
REPO="${REPO:-creditpulse}"
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
  command -v gcloud >/dev/null 2>&1 || die "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
  gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q . \
    || die "No active gcloud login. Run:  gcloud auth login"
  gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1 \
    || die "Project '$PROJECT_ID' not found or no access."
}

# ---- The digest the live Cloud Run revision is running (protect it) ---------
active_digest() {
  local rev img
  rev="$(gcloud run services describe "$SERVICE" --region "$REGION" \
         --format='value(status.traffic[0].revisionName)' 2>/dev/null)" || true
  [ -n "$rev" ] || return 0
  img="$(gcloud run revisions describe "$rev" --region "$REGION" \
         --format='value(spec.containers[0].image)' 2>/dev/null)" || true
  # img is either "<path>@sha256:<hex>" (pinned) or "<path>:latest"; emit the
  # sha256:<hex> when pinned so we can match it against the version list.
  case "$img" in *@sha256:*) echo "sha256:${img##*@sha256:}" ;; esac
}

# ---- list ------------------------------------------------------------------
list_images() {
  step "Images in ${IMAGE}"
  local active; active="$(active_digest)"
  [ -n "$active" ] && ok "Live revision runs digest: ${active:0:26}…" || warn "Could not resolve the live revision's digest."
  echo
  gcloud artifacts docker images list "$IMAGE" --include-tags \
    --format='table(version.slice(7:19):label=DIGEST, tags.list():label=TAGS, createTime.date("%Y-%m-%d %H:%M"):label=CREATED, buildTime)' \
    2>/dev/null || die "Could not list images (does the repo exist yet?)."
}

# ---- prune (default) -------------------------------------------------------
prune() {
  local dry="${1:-}"
  preflight
  local active; active="$(active_digest)"
  if [ -n "$active" ]; then
    ok "Protecting live revision digest: ${active:0:26}…"
  else
    warn "Could not resolve the live revision's digest — untagged-only filter still protects the tagged :latest."
  fi

  step "$([ "$dry" = dry ] && echo 'DRY RUN — untagged images that WOULD be deleted' || echo 'Deleting untagged images') in ${IMAGE}"
  local digests n=0 skipped=0
  digests="$(gcloud artifacts docker images list "$IMAGE" \
             --include-tags --filter='-tags:*' --format='value(version)' 2>/dev/null || true)"
  if [ -z "$digests" ]; then
    ok "No untagged images. Nothing to prune."
    return 0
  fi
  while IFS= read -r d; do
    [ -n "$d" ] || continue
    if [ "$d" = "$active" ]; then
      warn "skip (live revision)         ${d:0:26}…"
      skipped=$((skipped + 1)); continue
    fi
    if [ "$dry" = dry ]; then
      echo "  would delete  ${d:0:26}…"
    else
      gcloud artifacts docker images delete "${IMAGE}@${d}" --quiet >/dev/null 2>&1 \
        && ok "deleted  ${d:0:26}…" \
        || warn "failed   ${d:0:26}…  (may be referenced by a retained revision)"
    fi
    n=$((n + 1))
  done <<< "$digests"

  echo
  if [ "$dry" = dry ]; then
    echo "${BOLD}Dry run:${RST} ${n} untagged image(s) would be deleted; ${skipped} protected. Re-run without 'dry' to delete."
  else
    echo "${BOLD}${GREEN}Done.${RST} Pruned ${n} untagged image(s); ${skipped} protected. Live service untouched."
  fi
}

# ---- Dispatch --------------------------------------------------------------
case "${1:-prune}" in
  prune|"")     prune ;;
  dry|dry-run)  prune dry ;;
  list|ls)      preflight; list_images ;;
  -h|--help|help)
    sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//' ;;
  *)
    die "Unknown command '$1'. Run '$0 --help'." ;;
esac
