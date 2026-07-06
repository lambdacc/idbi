"""CreditPulse UI audit — capture views across data states and viewports.

Pairs with REPORT.md in this folder: same screenshot names, states and
viewports, so a before/after comparison is one re-run away. Prereqs: the app
running at BASE (`make demo` with PORT=8599, or edit BASE below),
`pip install playwright`, `playwright install chromium`. Output goes to
<repo-root>/ui-review/screenshots/ (gitignored evidence, not submission material).
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8599"
OUT = Path(__file__).resolve().parents[2] / "ui-review" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name, full=True):
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("  saved", name)


def wait_app(page):
    page.wait_for_selector("[data-testid='stAppViewContainer']", timeout=30000)
    page.wait_for_timeout(1500)


def run_assessment(page, entity_text, vp, capture_mid=False, mid_name=""):
    """From Home: pick entity, run, wait for pipeline completion."""
    page.goto(BASE, wait_until="domcontentloaded")
    wait_app(page)
    # pick the radio option containing entity_text
    page.get_by_text(entity_text, exact=False).first.click()
    page.wait_for_timeout(800)
    page.get_by_role("button", name="Run Assessment").click()
    # staged reveal starts on the Pipeline page
    if capture_mid:
        page.wait_for_timeout(4500)
        shot(page, mid_name, full=False)
    page.wait_for_selector("text=Assessment complete", timeout=120000)
    page.wait_for_timeout(800)


def nav_body_link(page, label_part):
    """Navigate via in-body page_link (works when sidebar is collapsed)."""
    # force=True: adjacent nav columns intercept pointer events (recorded as a finding)
    page.get_by_role("link", name=label_part).first.click(force=True)
    page.wait_for_timeout(2000)


def capture_entity(ctx, vp, entity_text, tag, views, capture_mid=False):
    page = ctx.new_page()
    run_assessment(page, entity_text, vp, capture_mid=capture_mid,
                   mid_name=f"pipeline-mid__{tag}__{vp}")
    if "pipeline" in views:
        shot(page, f"pipeline-complete__{tag}__{vp}")
    # Pipeline's health-card stage exposes a link to the full card
    if "healthcard" in views:
        nav_body_link(page, "Open the full Financial Health Card")
        shot(page, f"healthcard__{tag}__{vp}")
    if "explainability" in views:
        nav_body_link(page, "Why this score")
        shot(page, f"explainability__{tag}__{vp}")
    if "dashboard" in views:
        nav_body_link(page, "Dashboard")
        shot(page, f"dashboard__{tag}__{vp}")
    if "architecture" in views:
        # architecture link exists on Explainability page nav
        nav_body_link(page, "Architecture")
        shot(page, f"architecture__stateless__{vp}")
    page.close()


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- 1440 desktop: three entities ----------
    vp = "1440"
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page(); pg.goto(BASE, wait_until="domcontentloaded"); wait_app(pg)
    shot(pg, f"home__fresh__{vp}"); pg.close()

    capture_entity(ctx, vp, "Sunrise", "typical",
                   ["pipeline", "healthcard", "explainability", "dashboard"], capture_mid=True)
    capture_entity(ctx, vp, "Kirana", "thinfile", ["healthcard", "dashboard"])
    capture_entity(ctx, vp, "Auto", "inflated",
                   ["pipeline", "healthcard", "explainability", "architecture"])
    ctx.close()

    # ---------- 820 tablet: typical ----------
    vp = "820"
    ctx = browser.new_context(viewport={"width": 820, "height": 1100})
    pg = ctx.new_page(); pg.goto(BASE, wait_until="domcontentloaded"); wait_app(pg)
    shot(pg, f"home__fresh__{vp}"); pg.close()
    capture_entity(ctx, vp, "Sunrise", "typical", ["pipeline", "healthcard", "explainability"])
    ctx.close()

    # ---------- 390 mobile: typical + thin-file card ----------
    vp = "390"
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page(); pg.goto(BASE, wait_until="domcontentloaded"); wait_app(pg)
    shot(pg, f"home__fresh__{vp}"); pg.close()
    capture_entity(ctx, vp, "Sunrise", "typical",
                   ["pipeline", "healthcard", "explainability"], capture_mid=True)
    capture_entity(ctx, vp, "Kirana", "thinfile", ["healthcard"])
    ctx.close()

    # ---------- empty states: fresh sessions hitting inner pages ----------
    for vp, (w, h) in (("1440", (1440, 900)), ("390", (390, 844))):
        ctx = browser.new_context(viewport={"width": w, "height": h})
        pg = ctx.new_page()
        pg.goto(f"{BASE}/Financial_Health_Card", wait_until="domcontentloaded")
        wait_app(pg); shot(pg, f"healthcard__empty__{vp}")
        pg.goto(f"{BASE}/Dashboard", wait_until="domcontentloaded")
        wait_app(pg); shot(pg, f"dashboard__empty__{vp}")
        pg.close(); ctx.close()

    browser.close()
print("AUDIT CAPTURE DONE")
