# WP-V — Verification, docs, submission packaging (Wave 4)

**Goal:** prove the platform end-to-end, bring all public docs to platform framing, and stage the three-track submission. Runs after Waves 1–3; also acts as the integration referee for anything the parallel WPs left inconsistent.

## V1 — Full verification sweep
1. **Clean-checkout path:** in a scratch clone (or after `make clean`): `make install && make data-gen && make test && make demo` — document timings. Then `make prefit` twice (second run must skip all three engines).
2. **Test suite:** full `pytest app/tests -q` green; record the count delta vs 166 and per-WP additions.
3. **AppTest platform sweep** (extend the previous round's verify pattern; remember: seed session keys individually — SafeSessionState has no `.update`; find widgets by `key=`, never index): every registered page × {simple, technical} → 0 exceptions; jargon sweep on all Simple pages (Architecture exempt); T03 staged AND instant pipeline paths; T05 case page with a seeded `cp_case_account`.
4. **Cross-track consistency spot-check:** flagship archetype's T03 GST turnover vs T04 `altdata_monthly`; a current-account in T05 maps to a real MSME entity_id.
5. **Docker:** `make docker-build && make docker-run` — all three tracks served on `$PORT`; image size noted.
6. **Interaction affordances:** nav groups render grouped; Overview default; every `page_link/switch_page` resolves (crawl the registry and click-test via AppTest where possible); FOUC check by rapid nav.
7. **Determinism:** `make data-gen` twice → identical checksums for all CSVs.
8. **Selective-delete rehearsal (README acceptance #8):** scratch clones — delete t05 → green + 2 groups; delete t04 → green; delete both → PS3-only variant green. Document the exact `rm -rf` recipe per submission variant in the submission checklist.
9. **Deep links (README acceptance #9):** cold-session loads of `/`, `/track03`, `/track04`, `/track05` — locally AND on the deployed URL; record the three per-PS submission links.

## V2 — Documentation to platform framing (public repo = judged artifact)
- `README.md`: retitle to CreditPulse Platform; three-track table (PS3/PS4/PS5 + one-line each); quick start unchanged; per-track "what's under the hood" rows; keep the synthetic-data honesty block; update the in-app walkthrough paragraph.
- `START_HERE.md`: extend the map (new packages: `data_gen` additions, `ml/ews`, `ml/fraud`, both orchestrators, tracks registry, new pages); reading order updated.
- `docs/solution-design.md` + `docs/implementation-plan.md`: add concise Track-04/05 sections (design intent + module map; do not rewrite PS3 content).
- `docs/demo-script.md`: weave the WP-4A/5A raw sections into one 5-minute platform script — order: Overview (20s) → T03 (2 min, existing script compressed) → T04 (75s) → T05 (75s) → close (10s: one codebase, one deploy, FREE-AI-grade explainability).
- `pages/5_Architecture.py`: platform diagram (three tracks over shared data-gen/ml/backend/frontend layers), keep the honesty note; both view modes.
- `docs/business-impact-model.md`: add per-track impact stubs (T04: NPA lead-time value; T05: fraud-loss + ops-hours) with the same "illustrative planning estimate" health warning.
- `internal/issues`: append `→ Done/Deferred` annotations if any items were touched.

## V3 — Submission packaging (3 tracks)
- Portal reality check: confirm on Hack2skill that multi-track now allows one team → three PSs and whether each track needs a separate registration/PPT/deploy link. **Flag to founder immediately if the single-deploy-link assumption breaks.**
- Deploy once (existing runbook — Cloud Run); smoke the public URL; note cold-start behaviour (prefit baked into image per Dockerfile).
- PPT skeletons per track from the mandatory template (content bullets per track from the demo script + criteria mapping; PS3's existing criteria-mapping doc is the model — draft equivalents for T04/T05 in `internal/03-criteria-mapping/` as `criteria-mapping-t04.md` / `-t05.md`).
- Update `internal/submission-checklist.md` to a 3-track matrix (repo link, deploy link, PPT, demo video?) with owner/date columns.
- Repo hygiene decision check: `internal/` visibility in the public repo (existing known risk from `01-decision/DECISION-pending.md`) — re-raise to founder with options; do NOT act unilaterally.

## V4 — Memory + report
- Update the project memory (build-state + second-track files) with what shipped, counts, and gotchas.
- Final report to founder: acceptance checklist (README §6) item-by-item, metric headlines per track, open risks, and exactly what remains manual (PPT content, video, portal forms).

## Acceptance
README §6 global acceptance all checked; docs coherent under platform framing; submission checklist actionable; no uncommitted-work surprises (report git status; commits only if founder instructed).
