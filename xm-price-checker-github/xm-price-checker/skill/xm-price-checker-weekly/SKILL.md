---
name: "xm-price-checker-weekly"
description: "Weekly Xiaomi Poland competitor price check (colleague's Python+Excel XM Price Checker): run, read the check report, verify suspicious rows live, fix matching/links safely."
---

# XM Price Checker - weekly run and self-checks

Project: folder with `run_all.py`, `scrapers/`, `price_checks.py`, `link_builder.py`, workbook `XM_Price_Checker_Python.xlsm` (sheets Products / Links / RawData / Results / Settings). It exists in two copies (local launchers and PyCharm); apply every code change to BOTH.

## Weekly flow
1. The user updates Results (`RRP after Promotion`, offer start/end dates), adds Products rows if needed, saves and CLOSES Excel.
2. New product -> `python link_builder.py new <xlsm> <TargetID> --sites ...`; never hand-write search links. Hand-tuned search texts live in `link_overrides.json`.
3. Test run `python run_all.py --sites MSH --dry-run`, then the full `python run_all.py`. The workbook is backed up automatically before saving.
4. Read `<workbook>_check_report.txt`: HIGH and MEDIUM first. Rows scraped before the current promotion start date are ignored by the report.

## Business rules
- MSH (MediaMarkt): official shop only. A card whose text says `Sprzedaż i wysyłka przez XX` with XX not MediaMarkt (or has a marketplace seller link) is marketplace -> excluded. No seller line = official (do NOT add stricter rules such as requiring a pickup marker).
- Product matching must be correct but NOT over-strict: `RM` = Redmi; a missing `5G` in a title is fine; reject only on a real contradiction (target 5G vs title 4G/LTE or the reverse). Keep 5G strict only when Products holds both a 4G and a 5G version of the same name (e.g. Redmi Note 17 / Redmi Note 17 5G, Redmi Pad 2 Pro / Redmi Pad 2 Pro 5G). Model suffixes Pro / Max / Ultra / Lite / Plus always distinguish models.
- Price = current price only, never a crossed-out/lowest/instalment/refurbished amount.
- `euro.py` is unfinished (anti-bot) and unused.

## Self-check habits (do these without being asked)
- After any run, treat silent problems as bugs: a site column that is empty, a row 'not found/unavailable' without a price, a promo price above RRP, a price far from the other sites.
- Verify suspicious 'not found' rows LIVE with the built-in browser: open the search URL, list the cards with their seller (`Sprzedaż i wysyłka przez ...`) and price, and decide if the tool was right (e.g. only marketplace sellers = correctly excluded) or wrong (official card missed -> fix matching, add a unit test).
- Do not trust the log alone: the log the user pastes is often only the tail; read the generated check report or ask for the specific target's block.
- When a rule is changed after user feedback, add a unit test for it and run `python -m unittest tests.test_msh tests.test_price_checks tests.test_link_builder` before delivering.
- Only change the scraper that has the problem; say plainly which other scrapers were NOT touched.
- Promo > RRP values are the user's data: flag them, do not silently correct them.

## Environment pitfalls
- Shell/cloud cannot reach the retail sites (proxy 403): use the built-in browser for live checks, never curl around it; real scraping runs on the user's own Mac/PC.
- Playwright Chromium download may time out; `scrapers/browser_runner.py` falls back to installed Chrome, then Edge.
- `requests` must be in requirements; scraper modules are imported lazily so one broken module cannot stop the others.
- PyCharm: open the project FOLDER itself (not a file or a parent folder), reuse the existing `venv` as interpreter.
- Never edit the workbook with openpyxl-only shortcuts that drop VBA; use keep_vba or surgical zip edits, always keep a backup.

## Report
State: date, sites done/blocked, abnormal rows and how each was verified, links fixed, what the user must do.
## More detail
Setup/run/PyCharm/browser/result problems and their fixes: see references/TROUBLESHOOTING.md (symptom -> cause -> fix, all met in real use).
