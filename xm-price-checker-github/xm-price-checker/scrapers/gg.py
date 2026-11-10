# Not using for now, the availability detection is complicated and may not be reliable.

import re


print(
    "GG MODULE PATH:",
    __file__
)


# ============================================================
# PRICE
# ============================================================

def clean_price(text):

    if not text:
        return None

    text = str(text).strip()

    text = text.replace("\xa0", " ")

    # --------------------------------------------------------
    # Polish price format
    #
    # 549,00 zł
    # 449,00 zł
    # 399,00 zł
    # --------------------------------------------------------

    match = re.search(
        r"(\d[\d\s]*[,.]\d{2})\s*zł",
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


# ============================================================
# EXTRACT PRICE
# ============================================================

def extract_price(card_text):

    if not card_text:
        return None

    # --------------------------------------------------------
    # Find all prices
    #
    # Example:
    #
    # Regular price: 549,00 zł
    # 449,00 zł
    # Lowest price in 30 days before discount: 399,00 zł
    #
    # We want:
    #
    # 449,00 zł
    # --------------------------------------------------------

    matches = re.findall(
        r"\d[\d\s]*[,.]\d{2}\s*zł",
        card_text,
        re.IGNORECASE
    )

    if not matches:
        return None

    prices = [
        clean_price(price)
        for price in matches
    ]

    prices = [
        price
        for price in prices
        if price is not None
    ]

    if not prices:
        return None

    # --------------------------------------------------------
    # GG search result structure
    #
    # [0] Regular price
    # [1] Current selling price
    # [2] Lowest price in 30 days
    #
    # Example:
    #
    # 549.00
    # 449.00  <- current price
    # 399.00
    # --------------------------------------------------------

    if len(prices) >= 3:

        return prices[1]

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if len(prices) == 2:

        return prices[1]

    return prices[0]


# ============================================================
# COLOR
# ============================================================

def get_color(title):

    title_lower = title.lower()

    # --------------------------------------------------------
    # English colors
    # --------------------------------------------------------

    if "black" in title_lower:
        return "Black"

    elif "green" in title_lower:
        return "Green"

    elif "blue" in title_lower:
        return "Blue"

    elif "white" in title_lower:
        return "White"

    elif "grey" in title_lower:
        return "Grey"

    elif "gray" in title_lower:
        return "Grey"

    elif "silver" in title_lower:
        return "Silver"

    elif "gold" in title_lower:
        return "Gold"

    elif "purple" in title_lower:
        return "Purple"

    elif "pink" in title_lower:
        return "Pink"

    elif "red" in title_lower:
        return "Red"

    # --------------------------------------------------------
    # Polish colors
    # --------------------------------------------------------

    elif "czarny" in title_lower:
        return "Black"

    elif "czarna" in title_lower:
        return "Black"

    elif "czarne" in title_lower:
        return "Black"

    elif "zielony" in title_lower:
        return "Green"

    elif "zielona" in title_lower:
        return "Green"

    elif "zielone" in title_lower:
        return "Green"

    elif "niebieski" in title_lower:
        return "Blue"

    elif "niebieska" in title_lower:
        return "Blue"

    elif "niebieskie" in title_lower:
        return "Blue"

    elif "biały" in title_lower:
        return "White"

    elif "biała" in title_lower:
        return "White"

    elif "białe" in title_lower:
        return "White"

    elif "szary" in title_lower:
        return "Grey"

    elif "szara" in title_lower:
        return "Grey"

    elif "szare" in title_lower:
        return "Grey"

    elif "srebrny" in title_lower:
        return "Silver"

    elif "srebrna" in title_lower:
        return "Silver"

    elif "srebrne" in title_lower:
        return "Silver"

    elif "złoty" in title_lower:
        return "Gold"

    elif "złota" in title_lower:
        return "Gold"

    elif "złote" in title_lower:
        return "Gold"

    elif "Pomarańczowy" in title_lower:
        return "Orange"

    elif "fioletowy" in title_lower:
        return "Purple"

    elif "fioletowa" in title_lower:
        return "Purple"

    elif "fioletowe" in title_lower:
        return "Purple"

    elif "różowy" in title_lower:
        return "Pink"

    elif "różowa" in title_lower:
        return "Pink"

    elif "różowe" in title_lower:
        return "Pink"

    elif "czerwony" in title_lower:
        return "Red"

    elif "czerwona" in title_lower:
        return "Red"

    elif "czerwone" in title_lower:
        return "Red"

    elif "tytanowy" in title_lower:
        return "Titanium"

    elif "tytanowa" in title_lower:
        return "Titanium"

    elif "tytanowe" in title_lower:
        return "Titanium"

    else:
        return "Unknown"


# ============================================================
# RAM
# ============================================================

def get_ram(title):

    # --------------------------------------------------------
    # GG title format:
    #
    # Xiaomi Redmi A7 Pro 4+64GB Black smartphone
    #
    # RAM = 4
    # --------------------------------------------------------

    match = re.search(
        r"(\d+)\s*\+\s*\d+\s*GB",
        title,
        re.IGNORECASE
    )

    if match:

        return match.group(1) + " GB"

    return "Unknown"


# ============================================================
# STORAGE
# ============================================================

def get_storage(title):

    # --------------------------------------------------------
    # GG title format:
    #
    # Xiaomi Redmi A7 Pro 4+64GB Black smartphone
    #
    # Storage = 64
    # --------------------------------------------------------

    match = re.search(
        r"\d+\s*\+\s*(\d+)\s*GB",
        title,
        re.IGNORECASE
    )

    if match:

        return match.group(1) + " GB"

    return "Unknown"


# ============================================================
# GET PRODUCTS
# ============================================================

def get_products(page, product):

    results = []

    print(
        "Waiting for GG products..."
    )

    # --------------------------------------------------------
    # Wait for product headings
    # --------------------------------------------------------

    try:

        page.wait_for_selector(
            "h1, h2, h3, h4",
            timeout=15000
        )

    except Exception:

        print(
            "Could not find GG product headings."
        )

        return [{
            "product_name": product["name"],
            "variant": "Unknown",
            "ram": f'{product["ram"]} GB',
            "storage": f'{product["storage"]} GB',
            "price": None,
            "availability": "Unavailable"
        }]

    # --------------------------------------------------------
    # Find headings
    # --------------------------------------------------------

    headings = page.locator(
        "h1, h2, h3, h4"
    )

    count = headings.count()

    print(
        "GG H1/H2/H3/H4 count:",
        count
    )

    # --------------------------------------------------------
    # Target RAM / Storage
    # --------------------------------------------------------

    target_ram = re.sub(
        r"\D",
        "",
        str(product["ram"])
    )

    target_storage = re.sub(
        r"\D",
        "",
        str(product["storage"])
    )

    product_index = 0

    # ========================================================
    # LOOP THROUGH HEADINGS
    # ========================================================

    for i in range(count):

        heading = headings.nth(i)

        try:

            title = (
                heading
                .inner_text()
                .strip()
            )

        except Exception:

            continue

        print()
        print(
            f"GG TITLE {i}:",
            repr(title)
        )

        # ----------------------------------------------------
        # Product name matching
        # ----------------------------------------------------

        if (
            product["name"].lower()
            not in title.lower()
        ):

            continue

        # ----------------------------------------------------
        # RAM
        # ----------------------------------------------------

        ram = get_ram(
            title
        )

        # ----------------------------------------------------
        # STORAGE
        # ----------------------------------------------------

        storage = get_storage(
            title
        )

        # ----------------------------------------------------
        # Match RAM / Storage
        # ----------------------------------------------------

        if (
            re.sub(r"\D", "", str(ram))
            != target_ram
            or
            re.sub(r"\D", "", str(storage))
            != target_storage
        ):

            print(
                "RAM/storage does not match target."
            )

            continue

        # ----------------------------------------------------
        # COLOR
        # ----------------------------------------------------

        color = get_color(
            title
        )

        print()
        print(
            "=" * 60
        )
        print(
            f"GG PRODUCT {product_index}"
        )
        print(
            "=" * 60
        )

        print(
            "TITLE:",
            title
        )

        print(
            "RAM:",
            ram
        )

        print(
            "STORAGE:",
            storage
        )

        print(
            "COLOR:",
            color
        )

        # ----------------------------------------------------
        # Find product card
        # ----------------------------------------------------

        card = None

        # Try article first
        try:

            candidate = heading.locator(
                "xpath=ancestor::article[1]"
            ).first

            if candidate.count() > 0:

                card = candidate

        except Exception:

            pass

        # Fallback: walk up several levels
        if card is None:

            for level in range(1, 7):

                try:

                    candidate = heading.locator(
                        "xpath=" + "/.." * level
                    )

                    candidate_text = (
                        candidate
                        .inner_text()
                        .strip()
                    )

                    if (
                        "Regular price" in candidate_text
                        or
                        "Lowest price" in candidate_text
                    ):

                        card = candidate

                        break

                except Exception:

                    continue

        # ----------------------------------------------------
        # Card text
        # ----------------------------------------------------

        if card is not None:

            try:

                card_text = (
                    card
                    .inner_text()
                    .strip()
                )

            except Exception:

                card_text = title

        else:

            card_text = title

        print()
        print(
            "GG CARD TEXT:"
        )
        print(
            "-" * 60
        )
        print(
            card_text
        )
        print(
            "-" * 60
        )

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price = extract_price(
            card_text
        )

        print(
            "PRICE:",
            price
        )

        # ----------------------------------------------------
        # AVAILABILITY
        #
        # GG does not display an explicit availability
        # message in the search card.
        #
        # Based on the verified website behavior:
        #
        # Matching product + price = Available
        #
        # If the product does not appear in search results,
        # it will be handled after the loop as Unavailable.
        # ----------------------------------------------------

        if price is not None:

            availability = "Available"

        else:

            availability = "Unknown"

        print(
            "AVAILABILITY:",
            availability
        )

        # ----------------------------------------------------
        # SAVE RESULT
        # ----------------------------------------------------

        results.append({

            "product_name":
                product["name"],

            "variant":
                color,

            "ram":
                ram,

            "storage":
                storage,

            "price":
                price,

            "availability":
                availability
        })

        product_index += 1

    # ========================================================
    # PRODUCT NOT FOUND
    # ========================================================

    if not results:

        print()
        print(
            "=" * 60
        )
        print(
            "GG: MATCHING PRODUCT NOT FOUND"
        )
        print(
            "=" * 60
        )

        results.append({

            "product_name":
                product["name"],

            "variant":
                "Unknown",

            "ram":
                f'{product["ram"]} GB',

            "storage":
                f'{product["storage"]} GB',

            "price":
                None,

            "availability":
                "Unavailable"
        })

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print(
        "=" * 60
    )
    print(
        "GG RESULTS:",
        len(results)
    )
    print(
        "=" * 60
    )

    for result in results:

        print(
            result
        )

    return results


# ============================================================
# UNIFIED SCRAPER INTERFACE
# ============================================================

def get_price(page, product=None):

    if product is None:

        return None

    return get_products(
        page,
        product
    )