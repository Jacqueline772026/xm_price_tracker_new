import sys

sys.stdout.reconfigure(
    encoding="utf-8"
)

sys.stderr.reconfigure(
    encoding="utf-8"
)

import json

import importlib

from scrapers import browser_runner

# Scraper modules are imported only when their website is actually checked,
# so a problem in one module (e.g. euro.py, which is unfinished) can never
# stop the other websites.
SCRAPER_MODULES = {
    "MEX": "mex",
    "XKOM": "xkom",
    "ELECTRO.PL": "electro",
    "KTR": "ktr",
    "MSH": "msh",
    "MAX ELECTRO": "max_electro",
    "AVANS": "avans",
    "NEONET": "neonet",
    "EURO": "euro",
}


def load_scraper(website):

    name = SCRAPER_MODULES.get(website)

    if name is None:
        return None

    return importlib.import_module("scrapers." + name)


def main():

    if len(sys.argv) != 4:
        print(
            "Usage: python run_price_check.py WEBSITE URL PRODUCT_JSON"
        )
        sys.exit(1)

    website = sys.argv[1].strip().upper()
    url = sys.argv[2]

    try:
        product = json.loads(sys.argv[3])
    except json.JSONDecodeError as e:
        print(
            "ERROR: Invalid product JSON:",
            str(e)
        )
        sys.exit(1)

    scraper = load_scraper(website)

    if scraper is None:
        print(
            f"ERROR: No scraper configured for {website}"
        )
        sys.exit(1)

    print("=" * 50)
    print("Website:", website)
    print("URL:", url)
    print("Product:", product)
    print("=" * 50)

    try:

        result = browser_runner.run_scraper(
            url,
            scraper,
            product
        )

        print(
            "RESULT_JSON:" +
            json.dumps(
                result,
                ensure_ascii=False
            )
        )

    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )

        sys.exit(1)


if __name__ == "__main__":
    main()