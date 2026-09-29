"""Capture the README/demo screenshots from a running app (headless Chromium via Playwright).

Usage: BR_TOKEN=$(databricks auth token -p blue-river -o json | jq -r .access_token) \
       uv run --with playwright python scripts/capture_screenshots.py <app-url> docs/screenshots
"""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leak_scan import find_leaks  # noqa: E402
from playwright.sync_api import sync_playwright
base, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
FLAG = ("Why is TX-184 considered high risk, what led to the corrective maintenance decision, "
        "and was there evidence of the problem before June 2026?")
def shot(pg, name, full=False):
    pg.screenshot(path=f"{out}/{name}.jpg", type="jpeg", quality=88, full_page=full)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5,
                        extra_http_headers={"Authorization": "Bearer " + os.environ["BR_TOKEN"]})
    pg = ctx.new_page()
    pg.goto(base + "/"); pg.wait_for_selector("text=Maintenance by component", timeout=90000); time.sleep(0.5)
    shot(pg, "01-command-center")
    shot(pg, "01b-command-center-full", full=True)
    pg.goto(base + "/assets/TX-184"); pg.wait_for_selector(".source", timeout=90000); time.sleep(0.5)
    shot(pg, "02-asset-360")
    pg.locator("text=Event timeline").first.scroll_into_view_if_needed(); pg.mouse.wheel(0, 330); time.sleep(0.6)
    shot(pg, "03-asset-360-timeline-evidence")
    pg.goto(base + "/operations-intelligence?asset=TX-184"); pg.wait_for_selector("text=Asset TX-184")
    pg.fill("textarea", FLAG); pg.click("button:has-text('Analyze')")
    time.sleep(4); shot(pg, "04-operations-intelligence-working")
    pg.wait_for_selector("text=Generated synthesis", timeout=240000); time.sleep(0.8)
    pg.locator(".analysis-result").scroll_into_view_if_needed()
    pg.evaluate("window.scrollTo(0, document.querySelector('.analysis-result').getBoundingClientRect().top + window.scrollY - 84)")
    time.sleep(0.6); shot(pg, "05-operations-intelligence-answer-evidence")
    chip = pg.locator(".answer-md button.cite-chip:not(.structured)").nth(3)
    chip.scroll_into_view_if_needed(); pg.mouse.wheel(0, -120); chip.click(); time.sleep(1.0)
    shot(pg, "06-operations-intelligence-citation-drilldown")
    data = pg.evaluate("""() => ({
      cited: [...document.querySelectorAll('.answer-md button.cite-chip')].map(b => b.textContent),
      warnings: [...document.querySelectorAll('.notice.warn li')].map(l => l.textContent),
      meta: document.querySelector('.analysis-result .card-title')?.textContent })""")
    pg.goto(base + "/assets/TX-999"); pg.wait_for_selector("text=Asset not found", timeout=60000); time.sleep(0.3)
    shot(pg, "07-unknown-asset-state")
    html = ""
    for path in ["/", "/assets/TX-184", "/operations-intelligence"]:
        pg.goto(base + path); time.sleep(2); html += pg.content()
    leaks = find_leaks(html)
    json.dump({"answer_chips": data["cited"], "warnings": data["warnings"], "meta": data["meta"], "leaks": leaks},
              open(f"{out}/capture.json", "w"), indent=1)
    print("leaks:", leaks, "| warnings:", data["warnings"], "|", data["meta"])
    b.close()
