---
name: design-studio
description: Review, critique, and redesign user interfaces — web, desktop, and mobile — and produce implementation-ready design documentation (not code). Use whenever the user wants to review, critique, audit, redesign, or modernize a UI; improve UX, accessibility, visual hierarchy, or information architecture; analyze a screenshot or mockup; review React/Next.js/Tailwind/HTML/CSS front-end code; run a WCAG accessibility audit; or prepare a design handoff for engineering. Trigger even when the user just shares a screenshot or a component and asks "what do you think" or "make this better," and even if they never say the word "design."
---

# Design Studio

Review an interface and produce implementation-ready design documentation. This skill reviews and documents — it does **not** write or modify application code, and does not ask whether implementation should start. If changes are wanted, a separate implementation task consumes this skill's output.

If a `web-design-guidelines` or `frontend-design` skill is available and source code is present, apply it and fold its findings into the review.

## Gather context before reviewing

Actually look at the thing before critiquing it:

- **Screenshot / mockup** — inspect it directly.
- **Running app** — navigate the key routes and capture what the user actually sees, including hover, focus, empty, loading, and error states where reachable.
- **Source code** — read the relevant components, styles, and the design tokens / theme file. Judge the system, not just one screen.

Then identify the primary users, their primary tasks, and the context of use. State assumptions only where an assumption changes a recommendation.

## Review from five lenses

Evaluate independently through each lens, then synthesize — the point is to catch what a single perspective misses.

- **Product design** — visual hierarchy, information density, whitespace, typography, balance, overall polish.
- **UX** — discoverability, navigation, user flow, cognitive load, friction, information architecture, error prevention. Ground findings in named heuristics (Nielsen, Norman, Fitts's Law, Hick's Law, progressive disclosure, recognition over recall) so they're arguable rather than taste.
- **Visual** — spacing, alignment, grid, color, contrast, iconography, consistency.
- **Accessibility** — WCAG 2.2 AA, keyboard navigation, focus order, semantic structure, target size, screen-reader labelling.
- **Frontend** (only when source exists) — component architecture, reuse, responsiveness, design-token consistency, maintainability.

## Make every finding evidence-based

Each finding states: **what**, **where** (the concrete evidence), **why it matters** (in terms of a named principle — cognitive load, scanability, affordance, contrast, task completion — not personal preference), **the fix**, and **expected impact**. If you can't name why it matters, cut it.

Prefer the smallest change that resolves the problem. Don't redesign for novelty. Dedupe findings that surface under multiple lenses.

## Severity scale

- **Critical** — blocks task completion, or fails WCAG A / poses a legal-compliance risk.
- **High** — significant friction or confusion, or a WCAG AA failure.
- **Medium** — measurable but non-blocking; slows or mildly confuses users.
- **Low** — polish, consistency, nice-to-have.

## Scale the output to the request

**Default: focused review, delivered in chat.** An executive summary plus prioritized findings (severity, evidence, why, fix). This covers "review this," "critique this page," "what do you think," "improve X." Keep it tight.

**Full document set, written to files.** Produce this only when the user asks for a redesign, spec, handoff, or "the full treatment" — or when a review surfaces enough to justify it. Write each document as a separate markdown file in `design-review/` in the working directory, then list the paths.

1. `00-executive-summary.md` — overall assessment, key strengths, highest-impact opportunities.
2. `01-design-review.md` — every finding as a row: severity, evidence, why it matters, recommendation, expected impact.
3. `02-redesign-proposal.md` — the improved experience: layout, hierarchy, components, typography, color, interaction states, responsive behavior. Include wireframes where they clarify.
4. `03-engineering-spec.md` — per recommendation: objective, components affected, implementation sketch, acceptance criteria, dependencies, priority. Descriptive, not executable.
5. `04-roadmap.md` — **P0** critical / **P1** high-value / **P2** future, ordered by impact-over-effort.
6. `05-handoff.md` — a self-contained brief for an implementation agent: goals, architecture assumptions, component responsibilities, design-token changes, responsive behavior, accessibility requirements, risks, definition of done. Detailed enough to implement with no further design questions.

## Wireframes

When a layout change is easier shown than described, sketch it in markdown / ASCII (boxes, labels, arrows). It communicates structure without pretending to be a mockup.

---

After delivering the review (or, in full mode, the handoff), stop and wait for the user's next instruction. Do not begin implementation.