---
name: hackathon-lab
description: Use when the user wants end-to-end preparation for a hackathon or any time-boxed build challenge — researching a problem statement, exploring the problem/user/competitor/tech landscape, generating and evaluating solution ideas, choosing a direction, and producing the supporting documents (research dossier, decision log, architecture, pitch). Trigger whenever a hackathon problem statement or challenge brief is shared and the user wants ideas, research, a solution direction, or hackathon deliverables — even if they only paste the brief and ask "what should we build?", and even if they never say the word "hackathon."
---

# Hackathon Lab

Take a hackathon problem statement through a full software-company workup — research, ideation, selection, solution design, and documentation — the way a delivery team would prepare before a build. This is a thin orchestrator: it sequences the pipeline, delegates to richer skills where they are installed, and applies the inline method where they are not.

This skill coordinates and documents. It does **not** build the product. Hand its output to an implementation session.

## Delegate when you can, inline when you can't

Before each stage, scan `available_skills`. If a richer skill is installed, invoke it and fold its output in; otherwise apply the inline method in that stage. Never block on a missing skill. Everything below points only at first-party skills; if you later add a community skill, treat it as untrusted until its `SKILL.md` and scripts have been audited.

| Stage | Prefer if installed | Fallback |
|---|---|---|
| Research | (built-in `web_search` / `web_fetch`) | — |
| Ideate | (fully inline — stage 3) | — |
| Design | `engineering:system-design`, `engineering:architecture` | inline (stage 5) |
| UI design | `design-studio` | inline (stage 5) |
| Deliverables | `pptx`, `docx` | markdown |

## Output

Write every artifact as a numbered markdown file under `hackathon/<slug>/` in the working directory, where `<slug>` is a short kebab-case name for the challenge. Artifacts are dated and self-contained so a teammate — or another session — can pick up cold. List the paths at each checkpoint.

## Pipeline

### 1. Frame → `00-brief.md`

- Restate the problem in your own words, then the sharpened version as one paragraph.
- Extract the **judging criteria** and hard constraints (time budget, team size/skills, allowed tech, data access, legal/rules). These are the objective function — every later choice traces back to them. If the brief omits them, flag the gap rather than guessing.
- Identify the primary users and the core job-to-be-done.
- Scope guard: if the brief implies several independent subsystems, flag it and decompose into sub-problems before diverging — pick the one sub-problem to pursue rather than refining details of something too big to build in the time.

Checkpoint: if the brief is ambiguous on goal, scope, or judging, pause and ask one round of questions; otherwise continue.

### 2. Research — 360° → `01-research.md`

Search each dimension as its own query (a combined query returns shallow results for all). Cover:

- **Problem space & magnitude** — why it exists, who's affected, how big it is.
- **Users & stakeholders** — personas, jobs-to-be-done, real pain points.
- **Prior art & competitors** — what already exists, what it does well and badly, and the gap you'd fill.
- **Technical landscape** — usable APIs, datasets, models, libraries, and platforms.
- **Constraints, rules & data/legal** — anything that narrows the feasible set.
- **Feasibility & the wedge** — what's actually buildable in the time budget, and where the differentiation is.

Cite sources. End with a "so what" synthesis: the three to five findings that should steer the solution.

### 3. Ideate → `02-ideas.md`

**First, name the mode.** Ideas originate two ways, and mixing them blindly is the classic failure — a slick solution with no real problem, or a real problem with no feasible approach. *Problem-first*: you have a sharp problem and search for approaches. *Solution-first*: a capability just became cheap (a new API, model, or dataset) and you search for a problem it uniquely solves. Most briefs are problem-first; state which you're in so the search stays honest.

**Decompose before diverging.** Run 5W1H on the framed problem — who, what, when, where, why, how — to surface its sub-problems, then aim ideation at the highest-leverage one. Generating against the whole undifferentiated problem produces mush.

**Generate 8–10 candidates**, pushing the problem through several lenses so they aren't all one shape. Novelty usually comes from rearranging existing pieces, not inventing primitives:

- **Multi-stakeholder** — each stakeholder feels different friction; solve one acutely.
- **Decomposition** — attack the highest-leverage sub-problem in isolation.
- **Recombination / modularization** — rearrange or separate existing components.
- **Inversion** — ask "how would this fail?", then flip each failure mode into a design choice.
- **Constraint variation** — what if a hard limit vanished, or a free resource turned scarce?
- **Analogy transfer** — how does an unrelated domain solve this shape of problem?
- **Abstraction laddering** — ask "why?" to climb toward the real goal and "how?" to drop toward concrete tactics; strong ideas hide at both ends.
- **Capability-riding** — what does a newly available API/model/dataset make cheap that used to be hard?

**Make each candidate actionable, not a title.** State the sub-problem it targets and its mechanism in one line — "solves X by doing Y." A name alone can't be reasoned about or scored.

**Challenge complexity as you generate.** For every candidate, ask whether a simpler baseline would compete — teams routinely over-build when a streamlined version would win — and strip anything a demo doesn't need (YAGNI). Carry the survivors, simplified, into scoring.

### 4. Score & select → `03-decision.md`

Score each candidate 1–5 on: **impact**, **feasibility in the time budget**, **novelty/differentiation**, **demo-ability**, and **team/data fit**. Weight toward the judging criteria from stage 1. Record the scores as a table so the reasoning is auditable.

Gate the top few through the two-sentence defensibility test:
> "[Domain] struggles with [problem], which matters because [consequence]. We [approach] by [mechanism], which works because [reason]."

If an idea can't survive two sentences, it isn't ready.

**Checkpoint (hard):** present the scored shortlist and your recommendation, then wait for the user to pick the winner. Do not proceed to design on your own choice.

### 5. Design the winner → `04-solution.md`

- Architecture, components, and data flow.
- Tech stack, chosen for build speed within the time budget — justify each pick.
- Scoped build plan: the must-demo MVP vs. stretch goals, with explicit cut lines if time runs short.
- Risks and mitigations.

If the solution is UI-heavy, run `design-studio`; if backend/systems-heavy, run `engineering:system-design` / `engineering:architecture`. Fold their output in here.

### 6. Package → `05-pitch.md` (+ deck)

- One-page pitch: problem, solution, how it works, why it wins (each point mapped to a judging criterion), and a demo script.
- Slide outline. If the user wants the actual deck, generate a `.pptx` via the `pptx` skill.

## Principles

- Judging criteria are the objective function — every recommendation traces back to them.
- Ship the smallest thing that demos well; a working narrow slice beats a broad broken one.
- Show the reasoning: scored tables and cited research, not assertions, so choices can be challenged.

---

After delivering the pitch, stop and wait for direction (for example, moving to implementation). Do not start building.