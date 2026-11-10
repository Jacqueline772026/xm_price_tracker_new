"""
XM Price Checker - one-command version of Notebooks/XM_Price_Checker.ipynb

Run:
    python run_all.py                        # all enabled links
    python run_all.py --sites MSH            # only some websites (quick test)
    python run_all.py --excel "other.xlsm"   # another workbook
    python run_all.py --dry-run              # scrape + checks, do NOT touch the workbook

What it does (same steps as the notebook):
    read Products/Links -> run each scraper -> automatic checks
    -> RawData + Results -> save workbook (a backup copy is made first)
"""

import argparse
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

_parser = argparse.ArgumentParser(description="XM Price Checker")
_parser.add_argument("--excel", help="workbook to use (default: XM_Price_Checker_Python.xlsm next to this file)")
_parser.add_argument("--sites", help="comma separated websites to run, e.g. MSH,MEX (default: all)")
_parser.add_argument("--dry-run", action="store_true", help="do not write to the workbook")
ARGS = _parser.parse_args()


def display(obj):
    """Notebook display() replacement for a normal terminal."""
    try:
        print(obj.to_string())
    except AttributeError:
        print(obj)

# ============================================================
# 1. SETUP
# ============================================================

from pathlib import Path
from datetime import datetime
import json
import subprocess
import sys

from openpyxl import load_workbook
import pandas as pd

project_folder = Path(__file__).resolve().parent

excel_file = (
    Path(ARGS.excel).expanduser().resolve()
    if ARGS.excel
    else project_folder / "XM_Price_Checker_Python.xlsm"
)

if not excel_file.exists():
    sys.exit(
        f"ERROR: workbook not found: {excel_file}\n"
        "First time? Copy templates/XM_Price_Checker_Python.template.xlsm "
        "to XM_Price_Checker_Python.xlsm in the project folder and fill in "
        "your prices (see docs/USAGE.md)."
    )

print("Project folder:", project_folder)
print("Excel exists:", excel_file.exists())


# ============================================================
# 2. LOAD EXCEL WORKBOOK
# ============================================================

workbook = load_workbook(
    excel_file,
    keep_vba=True
)

products_sheet = workbook["Products"]
links_sheet = workbook["Links"]
rawdata_sheet = workbook["RawData"]
results_sheet = workbook["Results"]

print("Workbook loaded successfully.")
print("Sheets:", workbook.sheetnames)
print("Products rows:", products_sheet.max_row)
print("Links rows:", links_sheet.max_row)
print("RawData rows:", rawdata_sheet.max_row)
print("Results rows:", results_sheet.max_row)


# ============================================================
# 3. LOAD PRODUCTS
# ============================================================

products = {}

for row in products_sheet.iter_rows(
    min_row=2,
    values_only=True
):
    if not row:
        continue

    model = row[1]
    name = row[2]
    ram = row[3]
    storage = row[4]

    if model is None or ram is None or storage is None:
        continue

    model = str(model).strip()
    ram = str(ram).strip()
    storage = str(storage).strip()

    target_id = f"{model}-{ram}-{storage}"

    products[target_id.upper()] = {
        "target_id": target_id,
        "name": str(name).strip() if name is not None else model,
        "model": model,
        "ram": ram,
        "storage": storage
    }

# Products that exist as BOTH a 4G and a 5G version under the same name
# (e.g. "Redmi Note 17" and "Redmi Note 17 5G"). For these the "5G" word
# must match exactly; for all other products a missing "5G" is fine.
import re as _re


def _base_name(name):
    return _re.sub(r"\s+", " ", _re.sub(r"\b5g\b", " ", str(name).lower())).strip()


_variants = {}

for _p in products.values():
    _variants.setdefault(_base_name(_p["name"]), set()).add(
        bool(_re.search(r"\b5g\b", str(_p["name"]).lower()))
    )

for _p in products.values():
    _p["has_5g_sibling"] = len(_variants[_base_name(_p["name"])]) > 1

print(
    "Products with a 4G + 5G pair:",
    sorted({p["name"] for p in products.values() if p["has_5g_sibling"]})
)

print("Products loaded:", len(products))

if products:
    print("Example:", next(iter(products.values())))


# ============================================================
# 4. LOAD ENABLED LINKS
# ============================================================

links = []

for row in links_sheet.iter_rows(
    min_row=2,
    values_only=True
):
    if not row:
        continue

    target_id = row[0]
    website = row[1]
    url = row[2]
    enabled = row[3]

    if (
        target_id
        and website
        and url
        and str(enabled).strip().upper() == "YES"
    ):
        links.append({
            "target_id": str(target_id).strip(),
            "website": str(website).strip().upper(),
            "url": str(url).strip()
        })

target_ids = sorted({
    item["target_id"].strip().upper()
    for item in links
})

print("Enabled links:", len(links))
print("Target IDs:", target_ids)

if ARGS.sites:
    wanted = {s.strip().upper() for s in ARGS.sites.split(",") if s.strip()}
    links = [item for item in links if item["website"] in wanted]
    target_ids = sorted({item["target_id"].strip().upper() for item in links})
    print("Only running websites:", sorted(wanted))
    print("Links after filter:", len(links))


# ============================================================
# 5. RUN PRICE CHECKER
# ============================================================

def run_price_check(website, url, product):
    """Run the website scraper in a separate Python process."""

    script = project_folder / "run_price_check.py"

    product_json = json.dumps(
        product,
        ensure_ascii=False
    )

    process = subprocess.run(
        [
            sys.executable,
            str(script),
            website,
            url,
            product_json
        ],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    # Keep scraper/browser logs visible in the notebook.
    print(process.stdout)

    if process.returncode != 0:
        print(process.stderr)

        # Put the real reason (last line of the traceback) into the report.
        lines = [
            l.strip()
            for l in (process.stderr or "").splitlines()
            if l.strip()
        ]
        reason = lines[-1][:300] if lines else "no error text"

        raise RuntimeError(
            f"{website} price check failed: {reason}"
        )

    for line in process.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            return json.loads(
                line.replace(
                    "RESULT_JSON:",
                    "",
                    1
                ).strip()
            )

    raise ValueError(
        f"No RESULT_JSON returned for {website}."
    )


# ============================================================
# 6. PRODUCT LOOKUP
# ============================================================

def get_product(target_id):
    """Return product information loaded from the Products sheet."""

    key = str(target_id).strip().upper()

    try:
        return products[key]
    except KeyError:
        raise ValueError(
            f"TargetID not found in Products: {target_id}"
        )


# ============================================================
# 7. PRICE COLLECTION
# ============================================================

all_results = []

for target_id in target_ids:

    product = get_product(target_id)

    print()
    print("=" * 60)
    print("TARGET:", target_id)
    print(
        "Product:",
        product["name"],
        "| RAM:", product["ram"],
        "| Storage:", product["storage"]
    )
    print("=" * 60)

    target_links = [
        item for item in links
        if item["target_id"].strip().upper() == target_id
    ]

    for item in target_links:

        website = item["website"]
        url = item["url"]

        print()
        print("-" * 50)
        print("Website:", website)
        print("URL:", url)

        try:
            results = run_price_check(
                website,
                url,
                product
            )

            print("SCRAPER RESULTS:", results)

            # No matching product is not a scraper error.
            if not results:
                print("No matching products found.")
                continue

            for result in results:
                all_results.append({
                    "run_time": datetime.now(),
                    "target_id": target_id,
                    "website": website,
                    "product_name": result.get(
                        "product_name",
                        product["name"]
                    ),
                    "variant": result.get("variant", ""),
                    "ram": result.get("ram", product["ram"]),
                    "storage": result.get("storage", product["storage"]),
                    "url": url,
                    "price": result.get("price"),
                    "currency": "PLN",
                    "availability": result.get(
                        "availability",
                        "Unknown"
                    ),
                    "status": "OK",
                    "error": ""
                })

        except Exception as e:
            print("ERROR:", str(e))

            all_results.append({
                "run_time": datetime.now(),
                "target_id": target_id,
                "website": website,
                "product_name": product["name"],
                "variant": "",
                "ram": product["ram"],
                "storage": product["storage"],
                "url": url,
                "price": None,
                "currency": "PLN",
                "availability": "Unknown",
                "status": "ERROR",
                "error": str(e)
            })

print()
print("=" * 60)
print("PRICE COLLECTION COMPLETE")
print("=" * 60)
print("Total results:", len(all_results))


# ============================================================
# 8. RESULTS / VERIFICATION
# ============================================================

results_df = pd.DataFrame(all_results)

print("Raw scraper results:", len(results_df), "rows")

if not results_df.empty:
    display(
        results_df[
            [
                "target_id",
                "website",
                "product_name",
                "variant",
                "ram",
                "storage",
                "price",
                "availability",
                "status",
                "error"
            ]
        ]
    )

    print()
    print("=" * 70)
    print("TARGET / WEBSITE SUMMARY")
    print("=" * 70)

    summary_df = (
        results_df
        .groupby(
            ["target_id", "website"],
            dropna=False
        )
        .agg(
            variants=("variant", "count"),
            available=(
                "availability",
                lambda x: (x == "Available").sum()
            ),
            unavailable=(
                "availability",
                lambda x: (x == "Unavailable").sum()
            ),
            prices=(
                "price",
                lambda x: x.notna().sum()
            ),
            errors=(
                "status",
                lambda x: (x == "ERROR").sum()
            )
        )
        .reset_index()
    )

    display(summary_df)
else:
    print("No scraper results were collected.")


# ============================================================
# 8b. AUTOMATIC CHECKS  (read before trusting the Results sheet)
# ============================================================
#
# Silent problems (a website returning nothing, a link searching the
# wrong memory size, two prices for one colour, a promotion price typed
# above the RRP ...) are listed here, most serious first.
# Only the flagged items need a human look - you do not have to
# re-check every cell.
#
# HIGH   = results probably missing or wrong
# MEDIUM = suspicious, quick look at the page
# LOW    = informational
# ============================================================

import importlib
import sys

if str(project_folder) not in sys.path:
    sys.path.insert(0, str(project_folder))

import price_checks

importlib.reload(price_checks)

check_findings = price_checks.run_checks(
    rows=all_results,
    links=links,
    products=products,
    promo=price_checks.promo_from_results_sheet(results_sheet),
)

print(price_checks.format_report(check_findings))

_report_text = price_checks.format_report(check_findings)
_report_file = excel_file.with_name(excel_file.stem + "_check_report.txt")
_report_file.write_text(_report_text, encoding="utf-8")
print("Check report saved:", _report_file)


# ============================================================
# 9. RAW DATA OUTPUT
# ============================================================
#
# The RawData sheet is append-only.
# If you want a fresh run instead of keeping historical rows,
# clear the existing RawData rows manually before running this cell.
# ============================================================

for _, result in results_df.iterrows():

    price = result["price"]

    # Pandas NaN -> blank Excel cell
    if pd.isna(price):
        price = None

    rawdata_sheet.append([
        result["run_time"],
        result["target_id"],
        result["website"],
        result["product_name"],
        result["variant"],
        result["url"],
        price,
        result["currency"],
        result["availability"],
        result["status"],
        result["error"]
    ])

print("RawData rows written:", len(results_df))


# ============================================================
# 10. GENERATE RESULTS SHEET
# ============================================================
#
# The Results sheet is the final report.
#
# IMPORTANT:
# - Matching between Products and RawData uses TargetID.
# - RRP is displayed but is NOT used for the comparison.
# - Only "RRP after Promotion" is used as the benchmark.
# - Offer start/end dates are copied to the report but are NOT used.
#
# Report logic for each website:
#
# 1. If all returned variants are Unavailable -> "unavailable"
#
# 2. Ignore unavailable variants.
#    Only available variants with a valid price are used.
#
# 3. If all available colours have the same price:
#
#    a. If the price equals the promotion price:
#       -> "OK"
#
#    b. If the price is different from the promotion price:
#       -> "<price>"
#
# 4. If available colours have different prices:
#
#    - Colours with the promotion price -> "OK <colour>"
#    - Colours with another price -> "<price> <colour>"
#    - Colours with the same price are grouped together.
#
# ============================================================

# ------------------------------------------------------------
# 10.1 NORMALIZE NUMBER
# ------------------------------------------------------------

def normalize_number(value):
    """
    Return a numeric value as float, or None.
    """

    if value is None or pd.isna(value):
        return None

    try:

        return float(value)

    except (TypeError, ValueError):

        return None


# ------------------------------------------------------------
# 10.2 NORMALIZE REPORT PRICE
# ------------------------------------------------------------

def normalize_report_price(value):
    """
    Convert a price into an integer for Results reporting.

    Decimal values are ignored.

    Examples:
    1899.99 -> 1899
    599.99  -> 599
    399.00  -> 399
    """

    price = normalize_number(value)

    if price is None:

        return None

    return int(price)


# ------------------------------------------------------------
# 10.3 FORMAT PRICE
# ------------------------------------------------------------

def format_price(price):
    """
    Convert a report price into clean text.

    Examples:
    1899 -> "1899"
    599  -> "599"
    """

    if price is None:

        return ""

    return str(int(price))


# ------------------------------------------------------------
# 10.4 BUILD ONE WEBSITE REPORT VALUE
# ------------------------------------------------------------

def build_report_value(
    raw_rows,
    promotion_price
):
    """
    Build the value that will be written into one
    website cell in Results H:O.
    """

    # --------------------------------------------------------
    # No scraper record at all
    # --------------------------------------------------------

    if not raw_rows:

        return ""

    # --------------------------------------------------------
    # Normalize promotion price for reporting
    #
    # Decimal values are ignored.
    # --------------------------------------------------------

    promotion_price = normalize_report_price(
        promotion_price
    )

    # --------------------------------------------------------
    # Separate available and unavailable variants
    # --------------------------------------------------------

    available_rows = []

    unavailable_count = 0

    for row in raw_rows:

        availability = str(
            row.get("availability", "")
        ).strip().lower()

        price = normalize_report_price(
            row.get("price")
        )

        # ----------------------------------------------------
        # Explicitly unavailable
        # ----------------------------------------------------

        if availability == "unavailable":

            unavailable_count += 1

            continue

        # ----------------------------------------------------
        # Valid available product
        # ----------------------------------------------------

        if (
            availability == "available"
            and price is not None
        ):

            available_rows.append(row)

    # --------------------------------------------------------
    # ALL VARIANTS UNAVAILABLE
    # --------------------------------------------------------

    if (
        not available_rows
        and unavailable_count > 0
    ):

        return "unavailable"

    # --------------------------------------------------------
    # No usable scraper result
    # --------------------------------------------------------

    if not available_rows:

        return ""

    # --------------------------------------------------------
    # Collect all available report prices
    #
    # Decimal values are ignored.
    # --------------------------------------------------------

    all_prices = [
        normalize_report_price(
            row.get("price")
        )
        for row in available_rows
    ]

    # --------------------------------------------------------
    # Remove invalid prices
    # --------------------------------------------------------

    all_prices = [
        price
        for price in all_prices
        if price is not None
    ]

    if not all_prices:

        return ""

    unique_prices = set(
        all_prices
    )

    # --------------------------------------------------------
    # CASE 1 AND CASE 2:
    #
    # All available colours have the same price.
    # --------------------------------------------------------

    if len(unique_prices) == 1:

        common_price = all_prices[0]

        # ----------------------------------------------------
        # CASE 1:
        # Same price as promotion price -> OK
        # ----------------------------------------------------

        if (
            promotion_price is not None
            and common_price == promotion_price
        ):

            return "OK"

        # ----------------------------------------------------
        # CASE 2:
        # Same price, but different from promotion price
        # -> return the price only
        # ----------------------------------------------------

        return format_price(
            common_price
        )

    # --------------------------------------------------------
    # CASE 3:
    #
    # Available colours have different prices.
    #
    # Group colours by report price.
    # --------------------------------------------------------

    price_groups = {}

    for row in available_rows:

        price = normalize_report_price(
            row.get("price")
        )

        if price is None:

            continue

        color = str(
            row.get("variant", "")
        ).strip()

        if not color:

            color = "Unknown"

        # ----------------------------------------------------
        # Create price group if it does not exist
        # ----------------------------------------------------

        if price not in price_groups:

            price_groups[price] = []

        # ----------------------------------------------------
        # Avoid duplicate colour names
        # ----------------------------------------------------

        existing_colors = {
            existing.lower()
            for existing in price_groups[price]
        }

        if color.lower() not in existing_colors:

            price_groups[price].append(
                color
            )

    # --------------------------------------------------------
    # Build final report groups
    # --------------------------------------------------------

    report_parts = []

    for price, colors in price_groups.items():

        color_text = ",".join(
            color.lower()
            for color in colors
        )

        # ----------------------------------------------------
        # Colours at promotion price
        # ----------------------------------------------------

        if (
            promotion_price is not None
            and price == promotion_price
        ):

            report_parts.append(
                f"OK {color_text}"
            )

        # ----------------------------------------------------
        # Colours at another price
        # ----------------------------------------------------

        else:

            price_text = format_price(
                price
            )

            report_parts.append(
                f"{price_text} {color_text}"
            )

    # --------------------------------------------------------
    # Separate different price groups with semicolons
    # --------------------------------------------------------

    return "; ".join(
        report_parts
    )

# ------------------------------------------------------------
# 10.5 READ WEBSITE HEADERS FROM RESULTS
# ------------------------------------------------------------

website_columns = [
    results_sheet.cell(
        1,
        col
    ).value
    for col in range(
        8,
        16
    )
]

print(
    "Results website columns:"
)

print(
    website_columns
)


# ------------------------------------------------------------
# 10.6 CREATE RAWDATA LOOKUP
# ------------------------------------------------------------

raw_lookup = {}

for _, raw_row in results_df.iterrows():

    target_id = str(
        raw_row["target_id"]
    ).strip().upper()

    website = str(
        raw_row["website"]
    ).strip().upper()

    key = (
        target_id,
        website
    )

    raw_lookup.setdefault(
        key,
        []
    ).append(
        raw_row.to_dict()
    )


# ------------------------------------------------------------
# 10.7 WRITE WEBSITE RESULTS
# ------------------------------------------------------------

result_row_number = 2

for product_row in products_sheet.iter_rows(
    min_row=2,
    values_only=True
):

    if not product_row:
        continue

    # --------------------------------------------------------
    # CURRENT PRODUCTS STRUCTURE
    # --------------------------------------------------------

    model = product_row[1]

    ram = product_row[3]

    storage = product_row[4]

    # --------------------------------------------------------
    # Skip invalid product rows
    # --------------------------------------------------------

    if (
        model is None
        or ram is None
        or storage is None
    ):

        continue

    model = str(
        model
    ).strip()

    ram = str(
        ram
    ).strip()

    storage = str(
        storage
    ).strip()

    # --------------------------------------------------------
    # Promotion price comes from Results
    # --------------------------------------------------------

    promotion_price = results_sheet.cell(
        result_row_number,
        5
    ).value

    # --------------------------------------------------------
    # Construct TargetID
    # --------------------------------------------------------

    target_id = (
        f"{model}-{ram}-{storage}"
    ).upper()

    print()
    print(
        "=" * 60
    )

    print(
        f"Generating Results for: {target_id}"
    )

    print(
        f"Promotion price: {promotion_price}"
    )

    # --------------------------------------------------------
    # WRITE WEBSITE RESULTS H:O
    # --------------------------------------------------------

    for offset, website_column in enumerate(
        website_columns,
        start=8
    ):

        # ----------------------------------------------------
        # Empty website header
        # ----------------------------------------------------

        if not website_column:
            continue

        website_key = str(
            website_column
        ).strip().upper()

        # ----------------------------------------------------
        # Find scraper results
        # ----------------------------------------------------

        raw_rows = raw_lookup.get(
            (
                target_id,
                website_key
            ),
            []
        )

        # ----------------------------------------------------
        # Build final report value
        # ----------------------------------------------------

        report_value = build_report_value(
            raw_rows,
            promotion_price
        )

        # ----------------------------------------------------
        # WRITE ONLY H:O
        # ----------------------------------------------------

        results_sheet.cell(
            result_row_number,
            offset
        ).value = report_value

        print(
            f"  {website_column}: {report_value}"
        )

    # --------------------------------------------------------
    # Next product row
    # --------------------------------------------------------

    result_row_number += 1


# ------------------------------------------------------------
# 10.8 FINISHED
# ------------------------------------------------------------

print()
print(
    "=" * 70
)

print(
    "WEBSITE RESULTS GENERATED"
)

print(
    "=" * 70
)

print(
    "Rows processed:",
    result_row_number - 2
)

print(
    "Website columns written:",
    website_columns
)

print(
    "Columns A:G were NOT modified."
)

print(
    "Only columns H:O were written."
)


# ------------------------------------------------------------
# 10.9 PREVIEW
# ------------------------------------------------------------

report_preview = pd.DataFrame(
    results_sheet.values
)

display(
    report_preview
)

# ============================================================
# 11. SAVE WORKBOOK  (backup first)
# ============================================================

if ARGS.dry_run:
    print("DRY RUN - workbook was not changed.")
else:
    backup = excel_file.with_name(
        f"{excel_file.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}{excel_file.suffix}"
    )
    shutil.copy2(excel_file, backup)
    print("Backup saved:", backup.name)

    workbook.save(excel_file)

    print("RawData and Results updated successfully.")
    print("Workbook saved:", excel_file)
