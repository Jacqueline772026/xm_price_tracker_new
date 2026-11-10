"""
price_checks.py - automatic sanity checks for XM Price Checker.

WHY
---
Most scraper problems are SILENT: a site returns nothing, a colour comes back
"Unknown", a link searches the wrong memory size, or two prices appear for the
same colour. The Results sheet then simply shows a blank or a wrong number and
nobody is told. These checks turn those silent problems into a short list, so
only the flagged items need a human look instead of every cell.

TWO WAYS TO RUN
---------------
1. Inside the Notebook (a cell was added after "RESULTS / VERIFICATION").
2. From a terminal, on the saved workbook (checks the latest run in RawData):

       python price_checks.py "XM_Price_Checker_Python.xlsm"

   A text report is also written next to the workbook (check_report.txt).
   The workbook itself is only READ, never modified.

SEVERITY
--------
HIGH   - Results are probably missing or wrong. Look before you use them.
MEDIUM - Suspicious value; usually a quick look at the page settles it.
LOW    - Informational / likely harmless.
"""

import os
import re
import statistics
import sys
import urllib.parse as urlparse
from collections import defaultdict
from datetime import datetime

# Price this far from the median of all sites is worth a look (LOW) ...
OUTLIER_RATIO = 0.10

# ... and this far is probably a wrong model / wrong listing (MEDIUM)
OUTLIER_STRONG_RATIO = 0.20

# Prices more than this fraction below "RRP after Promotion" are suspicious
TOO_HIGH_RATIO = 0.30
LAYOUT_UNKNOWN_RATIO = 0.30
TOO_LOW_RATIO = 0.30

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


# ------------------------------------------------------------
# helpers
# ------------------------------------------------------------

def _norm_site(value):
    return str(value or "").strip().upper()


def _norm_target(value):
    return str(value or "").strip().upper()


def _finding(severity, check, site, target, message):
    return {
        "severity": severity,
        "check": check,
        "site": site,
        "target": target,
        "message": message,
    }


def _number(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def _search_text(url):
    """The search words inside a retailer search URL, lower-cased."""
    parsed = urlparse.urlparse(str(url))
    params = urlparse.parse_qs(parsed.query)
    for key, values in params.items():
        if "query" in key.lower() or key == "q":
            return values[0].lower().replace("+", " ")
    return urlparse.unquote(str(url)).lower()


def _storage_number(storage):
    text = str(storage).strip().upper().replace(" ", "")
    if text in ("1T", "1TB"):
        return "1000"
    match = re.search(r"\d+", text)
    return match.group() if match else text


# ------------------------------------------------------------
# 1. LINK CHECKS (Links sheet vs Products sheet)
# ------------------------------------------------------------

def check_links(links, products):
    """
    products: {TARGET_ID_UPPER: {"name", "ram", "storage"}}
    links:    [{"target_id", "website", "url"}]  (enabled links)
    """

    findings = []

    for link in links:

        target = _norm_target(link["target_id"])
        site = _norm_site(link["website"])

        product = products.get(target)

        if product is None:
            findings.append(_finding(
                "HIGH", "link-target", site, target,
                "TargetID is not in the Products sheet.",
            ))
            continue

        name = str(product["name"]).lower().strip()
        ram = str(product["ram"]).strip()
        storage = _storage_number(product["storage"])
        text = _search_text(link["url"])

        text = re.sub(r"\brm\b", "redmi", text)   # RM = Redmi

        if name not in text:
            findings.append(_finding(
                "MEDIUM", "link-name", site, target,
                f"Search words '{text}' do not contain the product name "
                f"'{product['name']}'.",
            ))
            continue

        tail = text.split(name)[-1]
        digits = re.findall(r"\d+", tail)

        is_1tb = storage == "1000" and re.search(r"\b1\s*t(b)?\b", tail)

        if not digits and not is_1tb:
            findings.append(_finding(
                "LOW", "link-memory", site, target,
                "Search link has no memory size; the scraper must filter "
                f"{ram}/{product['storage']} by itself.",
            ))
            continue

        joined = "".join(digits)

        storage_ok = (
            is_1tb
            or storage in digits
            or joined.endswith(storage)
        )

        # RAM may be left out of the link (only the storage given)
        ram_ok = (
            bool(is_1tb)
            or ram in digits
            or joined.startswith(ram)
            or digits == [storage]
        )

        if not (storage_ok and ram_ok):
            findings.append(_finding(
                "HIGH", "link-memory", site, target,
                f"Search link asks for '{tail.strip()}' but the product is "
                f"{ram}/{product['storage']}. It will search the wrong "
                "memory version - fix the link in the Links sheet.",
            ))

    return findings


def check_links_generated(links, products, skip=()):
    """
    Compare every link with the one link_builder.py would generate from the
    Products sheet. A link that differs is a typo (or a new deliberate
    override that belongs in link_overrides.json).
    """

    try:
        import link_builder
    except ImportError:  # link_builder.py not next to this file
        return []

    overrides = link_builder.load_overrides()

    findings = []

    for link in links:

        target = _norm_target(link["target_id"])
        site = _norm_site(link["website"])

        if (site, target) in skip:
            continue

        product = products.get(target)

        if product is None or site not in link_builder.SITE_RULES:
            continue

        if not link_builder.same_link(
            link["url"], site, product, target, overrides
        ):
            expected = link_builder.search_text(
                site, product, target, overrides
            )

            findings.append(_finding(
                "MEDIUM", "link-differs", site, target,
                "Link searches "
                f"'{link_builder.decoded_search_text(link['url'])}' but the "
                f"Products sheet gives '{expected.lower()}'. Fix the link "
                "(python link_builder.py new ...) or, if it is deliberate, "
                "add it to link_overrides.json.",
            ))

    return findings


# ------------------------------------------------------------
# 2. RESULT CHECKS (one run of RawData)
# ------------------------------------------------------------

def _latest_run(rows):
    """Keep only the rows of the most recent run (by calendar day)."""

    def day(row):
        value = row.get("run_time")
        if isinstance(value, datetime):
            return value.date()
        return None

    days = [day(r) for r in rows if day(r) is not None]

    if not days:
        return rows

    latest = max(days)

    return [r for r in rows if day(r) in (latest, None)]


def _unknown_samples(limit=5):
    """Last distinct card texts the shared classifier could not read."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "unknown_availability.log")
    try:
        with open(path, encoding="utf-8") as f:
            lines = [x.strip() for x in f if x.strip()]
    except OSError:
        return []
    seen, out = set(), []
    for line in reversed(lines):
        key = line[-80:]
        if key not in seen:
            seen.add(key)
            out.append(line)
        if len(out) >= limit:
            break
    return out


def check_results(rows, links, promo=None):
    """
    rows:  list of dicts with keys target_id, website, variant, price,
           availability, status, error (RawData rows or notebook all_results)
    links: enabled links (to see which site/target pairs returned nothing)
    promo: {TARGET_ID: {"rrp": number, "promo": number}} (optional)
    """

    findings = []
    rows = _latest_run(rows)

    for row in rows:
        row["_site"] = _norm_site(row.get("website"))
        row["_target"] = _norm_target(row.get("target_id"))
        row["_price"] = _number(row.get("price"))
        row["_avail"] = str(row.get("availability") or "").strip().lower()
        row["_variant"] = str(row.get("variant") or "").strip()

    # ---- errors written by the notebook
    for row in rows:
        if str(row.get("status") or "").upper() == "ERROR":
            findings.append(_finding(
                "HIGH", "scraper-error", row["_site"], row["_target"],
                f"Scraper failed: {row.get('error') or 'no message'}",
            ))

    # ---- enabled links that produced no rows at all (silent blanks)
    have = defaultdict(int)
    for row in rows:
        have[(row["_target"], row["_site"])] += 1

    per_site_links = defaultdict(list)
    for link in links:
        per_site_links[_norm_site(link["website"])].append(
            _norm_target(link["target_id"])
        )

    for site, targets in per_site_links.items():

        missing = [t for t in targets if have.get((t, site), 0) == 0]

        if not targets:
            continue

        if len(missing) == len(targets):
            findings.append(_finding(
                "HIGH", "site-empty", site, "*",
                f"{site} returned NOTHING for all {len(targets)} enabled "
                "links. The website probably changed or blocked access; "
                "its Results column will be blank.",
            ))
        elif len(missing) > 0:
            findings.append(_finding(
                "MEDIUM", "site-gaps", site, "*",
                f"{site}: {len(missing)} of {len(targets)} links returned no "
                f"rows: {', '.join(sorted(missing))}",
            ))

    # ---- row level
    for row in rows:

        site, target = row["_site"], row["_target"]

        if row["_avail"] == "available" and row["_price"] is None:
            findings.append(_finding(
                "MEDIUM", "no-price", site, target,
                f"Available ({row['_variant'] or 'no colour'}) but no price was "
                "read. The report drops this row.",
            ))

        if row["_avail"] in ("unknown", ""):
            if str(row.get("status") or "").upper() != "ERROR":
                findings.append(_finding(
                    "MEDIUM", "availability-unknown", site, target,
                    f"Availability unknown ({row['_variant'] or 'no colour'}, "
                    f"price {row['_price']}). The report ignores this row.",
                ))

        if row["_avail"] == "available" and row["_price"] is not None:

            if row["_variant"].lower() in ("", "unknown"):
                findings.append(_finding(
                    "LOW", "colour-unknown", site, target,
                    f"Colour not recognised (price {row['_price']:g}); it is "
                    "reported as 'unknown' in Results.",
                ))

            if row["_price"] != int(row["_price"]):
                findings.append(_finding(
                    "LOW", "decimal-price", site, target,
                    f"Price {row['_price']} has decimals; Results cuts them "
                    f"off (shows {int(row['_price'])}).",
                ))

    # ---- layout-changed alarm: many unreadable cards on one site
    # Retailer pages change their wording from time to time. When a big share
    # of one site's cards has no readable stock status, the scraper's text
    # rules are out of date - say so loudly instead of leaving blanks.
    per_site = defaultdict(lambda: [0, 0])
    for row in rows:
        if str(row.get("status") or "").upper() == "ERROR":
            continue
        per_site[row["_site"]][0] += 1
        if row["_avail"] in ("unknown", ""):
            per_site[row["_site"]][1] += 1

    for site, (total, unknown) in per_site.items():
        if total >= 4 and unknown / total >= LAYOUT_UNKNOWN_RATIO:
            findings.append(_finding(
                "HIGH", "layout-changed", site, "*",
                f"{site}: {unknown} of {total} rows have no readable stock "
                "status. The page wording probably changed - update "
                "availability_markers.json with the new wording (see the "
                "'Unrecognised card text' lines below).",
            ))

    if any(f["check"] == "layout-changed" for f in findings):
        for sample in _unknown_samples():
            findings.append(_finding(
                "HIGH", "layout-changed", "-", "-",
                f"Unrecognised card text: ...{sample}",
            ))

    # ---- same colour, different prices
    # Results lists every different price (decimals are ignored there, so
    # they are ignored here too). This only tells you WHY a colour appears
    # twice, so it is LOW.
    groups = defaultdict(set)
    for row in rows:
        if row["_avail"] == "available" and row["_price"] is not None:
            groups[(row["_site"], row["_target"], row["_variant"].lower())].add(
                int(row["_price"])
            )

    for (site, target, colour), prices in groups.items():
        if len(prices) > 1:
            findings.append(_finding(
                "LOW", "same-colour-prices", site, target,
                f"Colour '{colour or 'unknown'}' has several prices "
                f"({', '.join(str(p) for p in sorted(prices))}) - probably a "
                "bundle / second listing. Results shows every price.",
            ))

    # ---- price far from the other sites
    by_target = defaultdict(list)
    for row in rows:
        if row["_avail"] == "available" and row["_price"] is not None:
            by_target[row["_target"]].append(row)

    seen = set()

    for target, items in by_target.items():

        sites = {r["_site"] for r in items}

        if len(sites) < 3:
            continue

        median = statistics.median(r["_price"] for r in items)

        reference_prices = []

        if promo and promo.get(target):
            for key in ("rrp", "promo"):
                value = _number(promo[target].get(key))
                if value:
                    reference_prices.append(value)

        for r in items:

            deviation = abs(r["_price"] - median) / median

            if deviation <= OUTLIER_RATIO:
                continue

            # A retailer selling exactly at RRP / promotion price is normal.
            if any(abs(r["_price"] - ref) / ref < 0.015
                   for ref in reference_prices):
                continue

            key = (r["_site"], target, r["_variant"], r["_price"])

            if key in seen:
                continue

            seen.add(key)

            findings.append(_finding(
                "MEDIUM" if deviation > OUTLIER_STRONG_RATIO else "LOW",
                "price-outlier", r["_site"], target,
                f"{r['_variant'] or 'colour ?'} {r['_price']:g} vs median "
                f"{median:g} of all sites "
                f"({(r['_price'] - median) / median:+.0%}).",
            ))

    # ---- against RRP / promotion price
    if promo:

        for target, items in by_target.items():

            info = promo.get(target)

            if not info:
                continue

            promo_price = _number(info.get("promo"))

            seen_rrp = set()

            for r in items:

                key = (r["_site"], r["_price"])

                if key in seen_rrp:
                    continue

                seen_rrp.add(key)

                # Only the promotion price is the reference (RRP is ignored).
                if promo_price and r["_price"] > promo_price * (1 + TOO_HIGH_RATIO):
                    findings.append(_finding(
                        "MEDIUM", "far-above-promo", r["_site"], target,
                        f"{r['_variant'] or 'colour ?'} {r['_price']:g} is more "
                        f"than {TOO_HIGH_RATIO:.0%} above the promotion price "
                        f"{promo_price:g} - likely another model or a wrong "
                        "link.",
                    ))

                if promo_price and r["_price"] < promo_price * (1 - TOO_LOW_RATIO):
                    findings.append(_finding(
                        "MEDIUM", "far-below-promo", r["_site"], target,
                        f"{r['_variant'] or 'colour ?'} {r['_price']:g} is more "
                        f"than {TOO_LOW_RATIO:.0%} below the promotion price "
                        f"{promo_price:g}.",
                    ))

    return findings


# ------------------------------------------------------------
# 3. INPUT-DATA CHECKS (Results sheet typed values)
# ------------------------------------------------------------

def check_promo_inputs(promo):

    findings = []

    for target, info in (promo or {}).items():

        promo_price = _number(info.get("promo"))

        # Promo above RRP is NOT flagged: the user's workbook values are
        # authoritative (they come from an import / comparison flow).

        if promo_price is None:
            findings.append(_finding(
                "MEDIUM", "promo-missing", "-", target,
                "No 'RRP after Promotion' value; OK / price cannot be decided.",
            ))

    return findings


# ------------------------------------------------------------
# public entry points
# ------------------------------------------------------------

# LOW checks that are summarised into one line per site
_SUMMARISE_BY_SITE = {"colour-unknown", "decimal-price", "link-memory"}


def merge_findings(findings):
    """
    Collapse repeats so the report stays short:
      - the same check on the same site+product becomes one line;
      - harmless LOW checks become one line per site.
    """

    merged = {}
    order = []

    for f in findings:

        if f["severity"] == "LOW" and f["check"] in _SUMMARISE_BY_SITE:
            key = (f["severity"], f["check"], f["site"], "*")
        else:
            key = (f["severity"], f["check"], f["site"], f["target"])

        if key not in merged:
            merged[key] = {**f, "target": key[3], "_messages": [],
                           "_targets": []}
            order.append(key)

        entry = merged[key]

        if f["message"] not in entry["_messages"]:
            entry["_messages"].append(f["message"])

        if f["target"] not in entry["_targets"]:
            entry["_targets"].append(f["target"])

    result = []

    for key in order:

        entry = merged[key]
        messages = entry.pop("_messages")
        targets = entry.pop("_targets")

        if key[3] == "*" and key[1] in _SUMMARISE_BY_SITE and key[0] == "LOW":
            entry["message"] = (
                f"{len(messages)} item(s), e.g. {messages[0]} "
                f"Products: {', '.join(targets[:12])}"
                + (" ..." if len(targets) > 12 else "")
            )
        else:
            shown = messages[:6]
            text = "  |  ".join(shown)
            if len(messages) > len(shown):
                text += f"  |  (+{len(messages) - len(shown)} more)"
            entry["message"] = text

        result.append(entry)

    return result


def run_checks(rows, links, products, promo=None):
    """Run every check and return findings sorted by severity."""

    findings = []
    findings += check_promo_inputs(promo)
    link_findings = check_links(links, products)
    findings += link_findings
    findings += check_links_generated(
        links, products,
        skip={(f["site"], f["target"]) for f in link_findings
              if f["severity"] != "LOW"},
    )
    if rows:  # no results yet (e.g. new week, nothing scraped) -> nothing to judge
        findings += check_results(rows, links, promo)
    findings = merge_findings(findings)

    findings.sort(
        key=lambda f: (SEVERITY_ORDER[f["severity"]], f["check"],
                       f["site"], f["target"])
    )

    return findings


def format_report(findings):

    counts = defaultdict(int)
    for f in findings:
        counts[f["severity"]] += 1

    lines = [
        "=" * 70,
        "PRICE CHECK - AUTOMATIC SANITY CHECKS",
        f"HIGH: {counts['HIGH']}   MEDIUM: {counts['MEDIUM']}   "
        f"LOW: {counts['LOW']}",
        "=" * 70,
    ]

    if not findings:
        lines.append("Nothing suspicious found.")
        return "\n".join(lines)

    current = None

    for f in findings:

        if f["severity"] != current:
            current = f["severity"]
            lines += ["", f"--- {current} ---"]

        lines.append(
            f"[{f['check']}] {f['site']} | {f['target']}: {f['message']}"
        )

    return "\n".join(lines)


# ------------------------------------------------------------
# workbook readers (read-only)
# ------------------------------------------------------------

def load_from_workbook(path):
    """Read Products / Links / RawData / Results from the xlsm (read-only)."""

    from openpyxl import load_workbook

    wb = load_workbook(path, data_only=True, read_only=True, keep_vba=False)

    products = {}
    for r in wb["Products"].iter_rows(min_row=2, values_only=True):
        if r and r[1] is not None and r[3] is not None and r[4] is not None:
            target = _norm_target(f"{str(r[1]).strip()}-{str(r[3]).strip()}-{str(r[4]).strip()}")
            products[target] = {
                "name": str(r[2]).strip() if r[2] else str(r[1]).strip(),
                "ram": str(r[3]).strip(),
                "storage": str(r[4]).strip(),
            }

    links = []
    for r in wb["Links"].iter_rows(min_row=2, values_only=True):
        if r and r[0] and r[1] and r[2] and str(r[3]).strip().upper() == "YES":
            links.append({
                "target_id": str(r[0]).strip(),
                "website": str(r[1]).strip(),
                "url": str(r[2]).strip(),
            })

    rows = []
    for r in wb["RawData"].iter_rows(min_row=2, values_only=True):
        if not r or r[0] is None:
            continue
        r = list(r) + [None] * (11 - len(r))
        rows.append({
            "run_time": r[0], "target_id": r[1], "website": r[2],
            "product_name": r[3], "variant": r[4], "url": r[5],
            "price": r[6], "currency": r[7], "availability": r[8],
            "status": r[9], "error": r[10],
        })

    promo = promo_from_results_sheet(wb["Results"])

    wb.close()

    return rows, links, products, promo


def promo_from_results_sheet(results_sheet):
    """
    {TARGET_ID: {"rrp", "promo"}} from the Results sheet
    (A=SKU, B=Memory like '12+1T', D=RRP, E=RRP after Promotion).
    Works with a normal or read-only worksheet.
    """

    promo = {}

    for r in results_sheet.iter_rows(min_row=2, values_only=True):

        if not r or r[0] is None or r[1] is None:
            continue

        memory = str(r[1]).strip().replace("+", "-")

        target = _norm_target(f"{str(r[0]).strip()}-{memory}")

        promo[target] = {"rrp": r[3], "promo": r[4]}

    return promo


def promo_start_date(path):
    """Latest 'offer start' date on the Results sheet (column F), or None."""

    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)

    try:
        dates = [
            r[5].date() if hasattr(r[5], "date") else r[5]
            for r in wb["Results"].iter_rows(min_row=2, values_only=True)
            if r and len(r) > 5 and hasattr(r[5], "year")
        ]
    finally:
        wb.close()

    return max(dates) if dates else None


def drop_stale_rows(rows, start):
    """
    Rows scraped BEFORE the current promotion started belong to the previous
    week. Checking them against this week's prices would give nonsense
    findings, so they are left out (and the caller says so).
    """

    if start is None:
        return rows, 0

    kept = []

    for r in rows:
        t = r.get("run_time")
        day = t.date() if hasattr(t, "date") else None

        if day is not None and day < start:
            continue

        kept.append(r)

    return kept, len(rows) - len(kept)


def main(argv):

    if len(argv) < 2:
        print(__doc__)
        return 2

    path = argv[1]

    rows, links, products, promo = load_from_workbook(path)

    start = promo_start_date(path)
    rows, stale = drop_stale_rows(rows, start)

    findings = run_checks(rows, links, products, promo)

    report = format_report(findings)

    if stale:
        report = (
            f"NOTE: {stale} RawData rows were scraped before the current "
            f"promotion started ({start}) and are ignored. Run the price "
            "check for this week first; until then only the promotion "
            "prices and the links are checked.\n\n" + report
        )

    print(report)

    out = path.rsplit(".", 1)[0] + "_check_report.txt"

    with open(out, "w", encoding="utf-8") as handle:
        handle.write(report + "\n")

    print("\nReport saved:", out)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
