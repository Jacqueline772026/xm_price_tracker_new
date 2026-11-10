#NOT WORKING FOR NOW!!
#OLEOLE BLOCKS ACCESS WITH ANTI BOTS

import re


print(
    "OLEOLE MODULE PATH:",
    __file__
)


# ============================================================
# Helpers
# ============================================================

def clean_price(text):

    if not text:
        return None

    match = re.search(
        r"(\d[\d\s]*[,.]?\d{0,2})\s*zł",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    value = (
        match.group(1)
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        return float(value)

    except ValueError:
        return None


def get_color(title):

    title_lower = title.lower()

    colors = {
        "czarny": "Black",
        "zielony": "Green",
        "niebieski": "Blue",
        "biały": "White",
        "szary": "Grey",
        "srebrny": "Silver",
        "złoty": "Gold",
        "fioletowy": "Purple",
        "różowy": "Pink",
        "czerwony": "Red",
        "tytanowy": "Titanium",
    }

    for polish, english in colors.items():

        if polish in title_lower:
            return english

    return "Unknown"


# ============================================================
# Product extraction
# ============================================================

def get_products(page, product):

    results = []

    print("Waiting for OLEOLE products...")

    page.wait_for_timeout(3000)

    # ========================================================
    # PAGE INSPECTION
    # ========================================================

    print()
    print("=" * 60)
    print("OLEOLE PAGE INSPECTION")
    print("=" * 60)

    print(
        "URL:",
        page.url
    )

    selectors = [
        "h1",
        "h2",
        "h3",
        "article",
        "[data-testid]",
        "[data-test]",
        "[class*='product']",
        "[class*='Product']",
        "[class*='card']",
        "[class*='Card']",
        "li",
    ]

    for selector in selectors:

        try:

            count = page.locator(selector).count()

            print(
                f"{selector} => {count}"
            )

        except Exception as e:

            print(
                f"{selector} => ERROR: {e}"
            )


    # ========================================================
    # BODY TEXT
    # ========================================================

    try:

        body = page.locator("body").inner_text()

        print()
        print("=" * 60)
        print("OLEOLE BODY TEXT")
        print("=" * 60)

        print(
            body[:20000]
        )

    except Exception as e:

        print(
            "BODY ERROR:",
            e
        )


    # ========================================================
    # PRODUCT-RELATED HEADINGS
    # ========================================================

    try:

        headings = page.locator("h1, h2, h3")

        total = headings.count()

        print()
        print("=" * 60)
        print("OLEOLE PRODUCT TITLE INSPECTION")
        print("=" * 60)

        print(
            "Total headings:",
            total
        )

        matching = []

        for i in range(total):

            try:

                text = headings.nth(i).inner_text().strip()

                if (
                    "Redmi" in text
                    or "Xiaomi" in text
                    or "A7" in text
                ):

                    matching.append(
                        (i, text)
                    )

            except Exception:
                continue


        print(
            "Matching headings:",
            len(matching)
        )

        for index, text in matching[:20]:

            print()
            print(
                "INDEX:",
                index
            )

            print(
                "TEXT:",
                text
            )


    except Exception as e:

        print(
            "HEADING INSPECTION ERROR:",
            e
        )


    # ========================================================
    # GENERIC PRODUCT-LIKE ELEMENTS
    # ========================================================

    for selector in [
        "[class*='product']",
        "[class*='Product']",
        "[class*='card']",
        "[class*='Card']",
    ]:

        try:

            elements = page.locator(selector)

            count = elements.count()

            print()
            print("=" * 60)
            print(
                "OLEOLE ELEMENT INSPECTION:",
                selector
            )
            print("=" * 60)

            print(
                "Total:",
                count
            )

            shown = 0

            for i in range(min(count, 20)):

                try:

                    text = (
                        elements
                        .nth(i)
                        .inner_text()
                        .strip()
                    )

                    if (
                        "Redmi" in text
                        or "Xiaomi" in text
                        or "A7" in text
                    ):

                        print()
                        print(
                            "--- ELEMENT",
                            i,
                            "---"
                        )

                        print(
                            text[:3000]
                        )

                        shown += 1

                except Exception:
                    continue

            print(
                "Matching elements shown:",
                shown
            )

        except Exception as e:

            print(
                "ELEMENT ERROR:",
                selector,
                e
            )


    print()
    print("=" * 60)
    print("OLEOLE INSPECTION FINISHED")
    print("=" * 60)

    print(
        "No results extracted yet."
    )

    return results