"""
link_builder.py - build the retailer search links from the Products sheet
instead of typing them by hand.

WHY
---
Typing links by hand caused the most serious silent errors: for example the
Avans link of "Redmi Note 17 Pro Max 8+512" asked for "8256", and the Electro
and Avans links of "Redmi Note 17 Pro 8+512" asked for "6256". The scraper then
read the wrong memory version and nothing flagged it.

HOW IT WORKS
------------
search text = product name (Products sheet) + memory in the site's style
    slash style   : "Redmi 17 4/128"        (MEX, MSH, KTR, XKOM, NEONET, Max electro)
    joined style  : "Redmi 17 4128"         (Electro.pl, Avans)
    1 TB phones   : "Xiaomi 17T Pro 5G 1TB" (no RAM, same on every site)

A few existing links were tuned by hand for a site (for example
"poco c95 pro 6 128", or "redmi pad 2 9.7\" 4/64"). Those exact texts are kept
in link_overrides.json, so today every link in the sheet equals what this
module would generate. From now on a link that does NOT equal the generated one
is a typo (or a new, deliberate override that should be added to the JSON).

USAGE (terminal, run in the project folder)
-------------------------------------------
Compare the Links sheet with the generated links (read-only):

    python link_builder.py check "XM_Price_Checker_Python 3.xlsm"

Create the rows for a NEW product (after adding it to the Products sheet),
ready to paste into the Links sheet:

    python link_builder.py new "XM_Price_Checker_Python 3.xlsm" P99-8-256
    python link_builder.py new "XM_Price_Checker_Python 3.xlsm" P99-8-256 --sites MEX,MSH,XKOM

The workbook is only READ. A CSV (TargetID, website, URL, Enable) is printed
and saved as new_links_<TargetID>.csv next to the workbook.
"""

import json
import os
import re
import sys
import urllib.parse as urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
OVERRIDES_FILE = os.path.join(HERE, "link_overrides.json")

# prefix        : everything before the search words
# memory        : "slash" -> 4/128      "joined" -> 4128
# space / slash : how a space and a "/" are written inside the URL
SITE_RULES = {
    "MEX": {
        "prefix": "https://www.mediaexpert.pl/search?query[menu_item]=&query[querystring]=",
        "memory": "slash", "space": "%20", "slash": "%2F"},
    "ELECTRO.PL": {
        "site": "Electro.pl",
        "prefix": "https://www.electro.pl/search?query[menu_item]=&query[querystring]=",
        "memory": "joined", "space": "%20", "slash": "%2F"},
    "AVANS": {
        "site": "Avans",
        "prefix": "https://www.avans.pl/search?query[menu_item]=&query[querystring]=",
        "memory": "joined", "space": "%20", "slash": "%2F"},
    "MSH": {
        "prefix": "https://mediamarkt.pl/pl/search.html?query=",
        "memory": "slash", "space": "%20", "slash": "%2F"},
    "KTR": {
        "prefix": "https://www.komputronik.pl/search/category/1?query=",
        "memory": "slash", "space": "+", "slash": "/"},
    "XKOM": {
        "prefix": "https://www.x-kom.pl/szukaj?q=",
        "memory": "slash", "space": "%20", "slash": "%2F"},
    "NEONET": {
        "prefix": "https://www.neonet.pl/szukaj?q=",
        "memory": "slash", "space": "%20", "slash": "%2F"},
    "MAX ELECTRO": {
        "site": "Max electro",
        "prefix": "https://maxelektro.pl/wyniki-wyszukiwania?query=",
        "memory": "slash", "space": "%20", "slash": "/"},
}


def site_key(site):
    return str(site or "").strip().upper()


def site_label(site):
    """The spelling used in the Links sheet / Results header."""
    key = site_key(site)
    return SITE_RULES[key].get("site", key)


def load_overrides(path=OVERRIDES_FILE):
    """{SITE_UPPER: {TARGET_UPPER: search text}}"""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    return {
        site_key(site): {str(t).upper(): text for t, text in items.items()}
        for site, items in raw.items()
        if not site.startswith("_")
    }


def is_1tb(storage):
    return str(storage).strip().upper().replace(" ", "") in ("1T", "1TB")


def search_text(site, product, target_id=None, overrides=None):
    """
    The words typed into the retailer's search box.
    product: {"name", "ram", "storage"}
    """

    key = site_key(site)

    if key not in SITE_RULES:
        raise ValueError(f"No link rule for website '{site}'")

    if overrides is None:
        overrides = load_overrides()

    if target_id is not None:
        custom = overrides.get(key, {}).get(str(target_id).upper())
        if custom:
            return custom

    name = str(product["name"]).strip()
    ram = str(product["ram"]).strip()
    storage = str(product["storage"]).strip()

    if is_1tb(storage):
        return f"{name} 1TB"

    if SITE_RULES[key]["memory"] == "joined":
        return f"{name} {ram}{storage}"

    return f"{name} {ram}/{storage}"


def encode(site, text):
    rule = SITE_RULES[site_key(site)]

    encoded = urlparse.quote(text, safe="/")

    encoded = encoded.replace("%20", rule["space"])

    encoded = encoded.replace("/", rule["slash"])

    return encoded


def build_url(site, product, target_id=None, overrides=None):
    key = site_key(site)
    text = search_text(site, product, target_id, overrides)
    return SITE_RULES[key]["prefix"] + encode(site, text)


def decoded_search_text(url):
    """Search words inside an existing link (decoded, lower-case)."""
    parsed = urlparse.urlparse(str(url))
    params = urlparse.parse_qs(parsed.query)
    for key, values in params.items():
        if "query" in key.lower() or key == "q":
            return values[0].lower().replace("+", " ").strip()
    return urlparse.unquote(str(url)).lower().strip()


def same_link(existing_url, site, product, target_id=None, overrides=None):
    """True when an existing link searches the same words the generator would."""
    expected = search_text(site, product, target_id, overrides)
    return decoded_search_text(existing_url) == expected.lower().strip()


# ------------------------------------------------------------------
# workbook level
# ------------------------------------------------------------------

def read_sheets(path):
    from openpyxl import load_workbook

    wb = load_workbook(path, data_only=True, read_only=True, keep_vba=False)

    products = {}
    for r in wb["Products"].iter_rows(min_row=2, values_only=True):
        if r and r[1] is not None and r[3] is not None and r[4] is not None:
            target = f"{str(r[1]).strip()}-{str(r[3]).strip()}-{str(r[4]).strip()}".upper()
            products[target] = {
                "name": str(r[2]).strip() if r[2] else str(r[1]).strip(),
                "ram": str(r[3]).strip(),
                "storage": str(r[4]).strip(),
            }

    links = []
    for r in wb["Links"].iter_rows(min_row=2, values_only=True):
        if r and r[0] and r[1] and r[2]:
            links.append({
                "target_id": str(r[0]).strip().upper(),
                "website": str(r[1]).strip(),
                "url": str(r[2]).strip(),
                "enabled": str(r[3]).strip().lower() if r[3] else "",
            })

    wb.close()

    return products, links


def compare(products, links, overrides=None):
    """Return (matching, differing, unknown_site, missing)."""

    if overrides is None:
        overrides = load_overrides()

    matching, differing, unknown = [], [], []

    have = set()

    for link in links:

        key = site_key(link["website"])
        target = link["target_id"]

        if key not in SITE_RULES:
            unknown.append(link)
            continue

        have.add((target, key))

        product = products.get(target)

        if product is None:
            differing.append((link, None, "TargetID is not in Products"))
            continue

        expected = search_text(key, product, target, overrides)

        if decoded_search_text(link["url"]) == expected.lower().strip():
            matching.append(link)
        else:
            differing.append((link, expected, "search words differ"))

    missing = [
        (target, key)
        for target in products
        for key in SITE_RULES
        if (target, key) not in have
    ]

    return matching, differing, unknown, missing


def new_rows(products, target_id, sites=None, overrides=None):
    """Links rows (TargetID, website, URL, Enable) for one product."""

    target = str(target_id).strip().upper()

    if target not in products:
        raise KeyError(
            f"{target} is not in the Products sheet - add the product there first."
        )

    if overrides is None:
        overrides = load_overrides()

    keys = (
        [site_key(s) for s in sites]
        if sites else list(SITE_RULES)
    )

    return [
        (target, site_label(k),
         build_url(k, products[target], target, overrides), "yes")
        for k in keys
    ]


def main(argv):

    if len(argv) < 3 or argv[1] not in ("check", "new"):
        print(__doc__)
        return 2

    path = argv[2]

    products, links = read_sheets(path)

    if argv[1] == "check":

        matching, differing, unknown, missing = compare(products, links)

        print(f"Links sheet: {len(links)} links")
        print(f"  identical to generated: {len(matching)}")
        print(f"  DIFFERENT from generated: {len(differing)}")
        print(f"  websites without a rule: {len(unknown)}")

        for link, expected, why in differing:
            print(f"\n  {link['website']} | {link['target_id']} ({why})")
            print(f"    in sheet : {decoded_search_text(link['url'])}")
            if expected:
                print(f"    expected : {expected.lower()}")

        print(f"\nProduct x website pairs with no link: {len(missing)} "
              "(often intended, e.g. tablets are not sold on every site)")

        return 1 if differing else 0

    if len(argv) < 4:
        print("Give the TargetID, e.g.  new <workbook> P99-8-256")
        return 2

    sites = None
    if "--sites" in argv:
        sites = argv[argv.index("--sites") + 1].split(",")

    rows = new_rows(products, argv[3], sites)

    lines = ["TargetID,website,URL,Enable"] + [
        ",".join(row) for row in rows
    ]

    print("\n".join(lines))

    out = os.path.join(
        os.path.dirname(os.path.abspath(path)),
        f"new_links_{argv[3].upper()}.csv",
    )

    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    print("\nSaved:", out)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
