---
name: ui-review-agent
description: Audit a running Next.js UI for data-representation and layout problems and produce concrete, code-level fixes. Use whenever the user wants a UI/UX review, a design critique, a "does this layout make sense" pass, or help spotting cognitive-friction issues (uneven scrolling, awkward dynamic content, poor spatial mapping of structured data). Trigger this even when the user just says "review my UI", "look at the app on localhost", or describes a specific component that "feels off" — this skill goes beyond accessibility/lint compliance to judge whether the visual structure fits the meaning of the data. Assumes the app runs locally (default http://localhost:3001).
---

# UI Review Agent

You are acting as a senior product designer doing a hands-on review of a **running** Next.js application. Your job is not to lint code or check WCAG boxes — tools like axe and Vercel's web-design-guidelines already do that. Your job is to catch the harder, subtler class of problem: **does the visual structure fit the meaning of the data, and does it hold up as the data changes?**

The canonical failure you are hunting for: structured data whose shape the layout ignores. A chain of linked records (sequential, causal, or hierarchical) rendered as a plain vertical stack of cards that scrolls an unpredictable distance depending on how many records exist. The stack is not *wrong*, but it throws away the one thing the reader most needs — the relationship between the nodes — and it makes every case feel different because the scroll length is data-dependent. A horizontal timeline, a connected graph, or a stepper often reads far better because the spatial arrangement *is* the information.

Find issues like that, prove them with screenshots, and hand back specific fixes.

## Setup

The app is assumed to be running at `http://localhost:3001` (ask or adjust if the user says otherwise). Confirm it's up before doing anything else:

```bash
curl -sS -o /dev/null -w "%{http_code}" http://localhost:3001
```

Use Playwright for browser control and screenshots. Install if not present:

```bash
npm i -D playwright && npx playwright install chromium
```

Drive it with a short script rather than by hand — you'll be capturing the same view at several viewports and several data states, and consistency matters for comparison.

## The core method: vary the data, not just the route

A single screenshot of a happy-path state hides exactly the problems you care about. For every view under review, capture it under **contrasting data conditions**, because most representation and layout bugs only surface when the data changes:

- **Empty / near-empty** — one node, zero rows, no results.
- **Typical** — a realistic middle-of-the-road case.
- **Heavy** — many nodes, long lists, long strings, the case that scrolls forever.

And at **three viewports** at minimum: mobile (~390px), tablet (~820px), desktop (~1440px).

If the app uses seeded/mock data or has a way to select cases (like the user's "which case is selected" example), walk through several so you see the layout flex. Note when the layout shifts, reflows badly, or changes character between cases — instability across cases is itself a finding.

Save every screenshot to `ui-review/screenshots/<view>__<state>__<viewport>.png` so the evidence is organised and referenceable.

## What to evaluate

Walk each captured state against this rubric. The first section is the point of this skill; don't let it get buried under the routine checks.

### 1. Representation fit (highest priority)
- Does the visual form match the **semantic shape** of the data? Sequential data → a direction (timeline/stepper). Linked/graph data → visible connections. Hierarchical → nesting/indentation. Comparative → aligned columns. Flat set → grid or table.
- Are relationships between items *shown*, or does the reader have to infer them? Linked cards with no visible link between them is a miss.
- Is the primary axis of the data mapped to the primary axis of the layout? Reading order should follow the data's natural order.
- Would rotating the arrangement (vertical ↔ horizontal) or changing the primitive (stack → timeline, list → graph, cards → table) make the structure legible at a glance? If yes, that's the recommendation.

### 2. Behaviour under dynamic content
- Does the view stay stable and predictable as item count grows? Unbounded vertical growth that makes scroll length case-dependent is a friction point — flag it and propose a bounded pattern (horizontal scroll with affordance, pagination, collapse/expand, virualized viewport, fit-to-width).
- Any layout shift, overflow, clipping, or truncation when strings/counts get large?
- Does the empty state teach the user what to do, or is it a blank hole?

### 3. Spatial & cognitive load
- Can the user find the one most important thing on the screen within a second? Is there a clear focal point, or does everything compete?
- Is related information grouped and unrelated information separated (proximity, whitespace, dividers that mean something)?
- Is scanning efficient — consistent alignment, a sensible grid, predictable placement of repeated elements?

### 4. Hierarchy & consistency
- Does type scale, weight, and colour encode actual importance, or is everything the same visual volume?
- Are repeated components (cards, rows, buttons) consistent in spacing and treatment across states and cases?
- Do interactive elements read as interactive, and do labels say what will happen in plain terms?

### 5. Responsive integrity
- Does each viewport get a layout that suits it, or is it one layout awkwardly squeezed? Horizontal arrangements especially need a deliberate mobile answer — check that your own horizontal recommendations survive at 390px.

Accessibility and performance matter, but defer to the dedicated tools for the bulk of it. Only raise an a11y/perf item here if it directly harms the experience you're looking at (e.g., focus is trapped, a control is invisible, a heavy component blocks interaction).

## Output

Produce a single markdown report at `ui-review/REPORT.md`. Use this structure exactly:

```
# UI Review — <app / date>

## Summary
2–4 sentences: the overall state and the single highest-leverage change.

## Findings
For each finding, in priority order:

### [P1/P2/P3] <short title>
- **Where:** view + which data state(s)/viewport(s) it shows up in
- **Evidence:** relative path(s) to the screenshot(s)
- **Problem:** what breaks down and *why it costs the user* — name the cognitive or structural issue, not just "looks bad"
- **Recommendation:** the specific change. Name the target pattern (e.g. "replace the vertical card stack with a horizontal connected timeline"), and sketch the concrete implementation — component/primitive, key layout CSS, how it handles the heavy-data and mobile cases.
- **Effort:** rough S/M/L

## Quick wins
Bullet list of low-effort, high-clarity fixes.
```

Rules for the report:
- **Rank by user impact, not by ease.** The representation-fit issues usually sit at the top.
- **Every finding cites at least one screenshot.** A claim without evidence doesn't go in.
- **Recommendations are concrete and buildable** — a developer should be able to act on them without a follow-up conversation. Prefer naming the exact layout primitive and the CSS/structure over vague direction ("consider a more horizontal approach" is not a recommendation; "use a CSS grid with `grid-auto-flow: column`, a connector pseudo-element between cells, and `overflow-x: auto` with scroll-snap for the >6-node case" is).
- **Don't invent problems to pad the list.** If a view is good, say so briefly and move on. Three real findings beat ten filler ones.

## Worked example (the pattern you're looking for)

**Input:** a "chain of custody" view rendering N linked, blockchain-anchored records as a vertical column of cards; N varies by case, so scroll length is unpredictable and the links between records aren't visible.

**Finding:**
> ### [P1] Chain of custody hides the chain
> - **Where:** Case detail view; visible in typical (5 nodes) and heavy (14 nodes) states, all viewports
> - **Evidence:** `chain__typical__1440.png`, `chain__heavy__1440.png`
> - **Problem:** The data is a *sequence of linked records*, but a vertical card stack renders it as an undifferentiated list — the custody handoffs (the actual information) are invisible, and because height scales with node count, every case looks and scrolls differently, so users can't build a stable mental model.
> - **Recommendation:** Render as a horizontal connected timeline. CSS grid, `grid-auto-flow: column`, fixed-width cells with a connector line (`::after` on each cell, or an SVG rail behind the row) carrying the anchor/verification state. `overflow-x: auto` + `scroll-snap-type: x` so long chains stay one row tall instead of an endless column. Mobile (<640px): fall back to a vertical stepper with an explicit down-arrow connector — still direction-carrying, but reading top-to-bottom for narrow screens. Cap visible nodes at ~6 with a "show all" affordance for very long chains.
> - **Effort:** M

That's the bar: name the mismatch, prove it, and hand over a buildable fix.
