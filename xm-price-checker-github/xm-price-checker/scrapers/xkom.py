import re

try:
    from . import matching      # imported as scrapers.<site> (normal case)
except ImportError:             # run as a plain script
    import matching


# ============================================================
# PRICE
# ============================================================

def clean_price(text):

    if not text:
        return None

    text = str(text)

    # Remove common labels/currency
    text = (
        text
        .replace("Cena:", "")
        .replace("zł", "")
        .replace("PLN", "")
        .strip()
    )

    # Match Polish price formats:
    #
    # 799
    # 799,00
    # 1 299
    # 1 299,00
    # 1 299,00

    match = re.search(
        r"\d{1,3}(?:[\s\u00a0\u202f]\d{3})*(?:[,.]\d{1,2})?",
        text
    )

    if not match:
        return None

    price_text = match.group(0)

    # Remove normal / non-breaking / narrow spaces
    price_text = (
        price_text
        .replace(" ", "")
        .replace("\u00a0", "")
        .replace("\u202f", "")
        .replace(",", ".")
    )

    try:
        return float(price_text)

    except ValueError:
        return None


# ============================================================
# COLOR
# ============================================================

def _get_color_base(title):

    title_lower = (
        str(title)
        .lower()
        .replace("\u00a0", " ")
    )

    # --------------------------------------------------------
    # Marketing colors first
    # --------------------------------------------------------

    if "glacier blue" in title_lower:
        return "Blue"

    elif "ocean blue" in title_lower:
        return "Blue"

    elif "sky blue" in title_lower:
        return "Blue"

    elif "ice blue" in title_lower:
        return "Blue"

    elif "ocean teal" in title_lower:
        return "Green"

    elif "forest green" in title_lower:
        return "Green"

    elif "midnight black" in title_lower:
        return "Black"

    elif "aurora purple" in title_lower:
        return "Purple"

    elif "mocha brown" in title_lower:
        return "Brown"

    # --------------------------------------------------------
    # English basic colors
    # --------------------------------------------------------

    elif re.search(r"\bblack\b", title_lower):
        return "Black"

    elif re.search(r"\bgreen\b", title_lower):
        return "Green"

    elif re.search(r"\bblue\b", title_lower):
        return "Blue"

    elif re.search(r"\bwhite\b", title_lower):
        return "White"

    elif re.search(r"\bgray\b", title_lower):
        return "Grey"

    elif re.search(r"\bgrey\b", title_lower):
        return "Grey"

    elif re.search(r"\bpurple\b", title_lower):
        return "Purple"

    elif re.search(r"\bsilver\b", title_lower):
        return "Silver"

    elif re.search(r"\bgold\b", title_lower):
        return "Gold"

    elif re.search(r"\bpink\b", title_lower):
        return "Pink"

    elif re.search(r"\bbrown\b", title_lower):
        return "Brown"

    elif re.search(r"\borange\b", title_lower):
        return "Orange"

    elif re.search(r"\btitanium\b", title_lower):
        return "Titanium"

    # --------------------------------------------------------
    # Polish colors
    # --------------------------------------------------------

    elif "czarn" in title_lower:
        return "Black"

    elif "zielon" in title_lower:
        return "Green"

    elif "niebiesk" in title_lower:
        return "Blue"

    elif "biały" in title_lower or "bialy" in title_lower:
        return "White"

    elif "szar" in title_lower:
        return "Grey"

    elif "srebr" in title_lower:
        return "Silver"

    elif "złot" in title_lower or "zlot" in title_lower:
        return "Gold"

    elif "fiolet" in title_lower:
        return "Purple"

    elif "Pomarańczowy" in title_lower:
        return "Orange"

    elif "róż" in title_lower or "roz" in title_lower:
        return "Pink"

    elif "brąz" in title_lower or "braz" in title_lower:
        return "Brown"

    elif "tytan" in title_lower:
        return "Titanium"

    else:
        return "Unknown"



def get_color(title):

    """Scraper colour list first, shared wide list as fallback."""

    colour = _get_color_base(title)

    if colour == "Unknown":
        colour = matching.detect_colour(title)

    return colour


# ============================================================
# PRODUCT MATCHING
# ============================================================

# ============================================================
# PRODUCT MATCHING
# ============================================================

def normalize_product_text(text):

    text = (
        str(text)
        .lower()
        .replace("\u00a0", " ")
        .strip()
    )

    # --------------------------------------------------------
    # Normalize Pro+
    # --------------------------------------------------------

    text = re.sub(
        r"\bpro\s*\+",
        "pro+",
        text
    )

    # --------------------------------------------------------
    # Replace punctuation with spaces
    # --------------------------------------------------------

    text = re.sub(
        r"[/(),;:_\-]+",
        " ",
        text
    )

    # --------------------------------------------------------
    # Keep letters, numbers, spaces and +
    # --------------------------------------------------------

    text = re.sub(
        r"[^a-z0-9ąćęłńóśźż+\s]",
        " ",
        text
    )

    # --------------------------------------------------------
    # Normalize spaces
    # --------------------------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def matches_product(title, product):

    title_normalized = normalize_product_text(
        title
    )

    target_normalized = normalize_product_text(
        product["name"]
    )

    print(
        "NORMALIZED TITLE:",
        title_normalized
    )

    print(
        "NORMALIZED TARGET:",
        target_normalized
    )

    # --------------------------------------------------------
    # STRICT 5G MATCHING
    # --------------------------------------------------------

    target_has_5g = bool(
        re.search(
            r"\b5g\b",
            target_normalized
        )
    )

    title_has_5g = bool(
        re.search(
            r"\b5g\b",
            title_normalized
        )
    )

    if target_has_5g != title_has_5g:

        print(
            "Product mismatch: 5G version does not match."
        )

        return False

    # --------------------------------------------------------
    # STRICT LTE MATCHING
    #
    # LTE is treated as a globally different product version.
    # --------------------------------------------------------

    target_has_lte = bool(
        re.search(
            r"\blte\b",
            target_normalized
        )
    )

    title_has_lte = bool(
        re.search(
            r"\blte\b",
            title_normalized
        )
    )

    if target_has_lte != title_has_lte:

        print(
            "Product mismatch: LTE version does not match."
        )

        return False

    # --------------------------------------------------------
    # SPECIAL 4G RULE — REDMI PAD 2 ONLY
    #
    # Prevent normal Redmi Pad 2 products from matching
    # Redmi Pad 2 4G.
    #
    # Does NOT affect:
    # - Redmi Pad 2 Pro
    # - Other Redmi products
    # - Other Xiaomi products
    # --------------------------------------------------------

    target_is_redmi_pad_2 = bool(
        re.match(
            r"^redmi pad 2(?:\s+\d+(?:\s+\d+)?)?$",
            target_normalized
        )
    )

    if target_is_redmi_pad_2:

        target_has_4g = bool(
            re.search(
                r"\b4g\b",
                target_normalized
            )
        )

        title_has_4g = bool(
            re.search(
                r"\b4g\b",
                title_normalized
            )
        )

        if target_has_4g != title_has_4g:

            print(
                "Product mismatch: Redmi Pad 2 4G "
                "version does not match."
            )

            return False

    # --------------------------------------------------------
    # Remove network labels after confirming versions match
    # --------------------------------------------------------

    target_core = re.sub(
        r"\b(5g|lte)\b",
        "",
        target_normalized
    )

    title_core = re.sub(
        r"\b(5g|lte)\b",
        "",
        title_normalized
    )

    target_core = re.sub(
        r"\s+",
        " ",
        target_core
    ).strip()

    title_core = re.sub(
        r"\s+",
        " ",
        title_core
    ).strip()

    target_tokens = target_core.split()

    title_tokens = title_core.split()

    # --------------------------------------------------------
    # Exact product-name token sequence
    # --------------------------------------------------------

    product_modifiers = {
        "pro",
        "pro+",
        "ultra",
        "max",
        "lite",
        "plus",
    }

    for start in range(
        len(title_tokens) - len(target_tokens) + 1
    ):

        end = start + len(target_tokens)

        # Exact sequence required
        if (
            title_tokens[start:end]
            != target_tokens
        ):

            continue

        # ----------------------------------------------------
        # Prevent base product matching a higher version
        #
        # Xiaomi 17
        # != Xiaomi 17 Pro
        # != Xiaomi 17 Ultra
        #
        # Redmi Note 15
        # != Redmi Note 15 Pro
        # != Redmi Note 15 Pro+
        # ----------------------------------------------------

        if end < len(title_tokens):

            next_token = title_tokens[end]

            if next_token in product_modifiers:

                print(
                    "Product mismatch: additional model "
                    f"version '{next_token}'."
                )

                continue

        print(
            "PRODUCT NAME MATCH: YES"
        )

        return True

    print(
        "Product name mismatch."
    )

    return False

# ============================================================
# RAM / STORAGE EXTRACTION
# ============================================================

def extract_ram_storage(title, card_text):

    ram = None
    storage = None

    # --------------------------------------------------------
    # Try card specifications first
    #
    # Examples:
    # Pamięć RAM: 12 GB
    # Pamięć wbudowana: 512 GB
    # Pamięć wbudowana: 1 TB
    # --------------------------------------------------------

    ram_match = re.search(
        r"Pamięć\s*RAM:\s*([0-9]+(?:\s*GB)?)",
        card_text,
        re.IGNORECASE
    )

    storage_match = re.search(
        r"Pamięć\s*wbudowana:\s*"
        r"([0-9]+(?:[.,][0-9]+)?\s*(?:GB|TB|T))",
        card_text,
        re.IGNORECASE
    )

    if ram_match:

        ram_value = ram_match.group(1).strip()

        # Add GB if the website only gives a number
        if not re.search(
            r"GB",
            ram_value,
            re.IGNORECASE
        ):

            ram_value += " GB"

        ram = ram_value

    if storage_match:

        storage = (
            storage_match
            .group(1)
            .strip()
        )

    # --------------------------------------------------------
    # Fallback: title formats
    #
    # Examples:
    #
    # 12/512GB
    # 12GB/512GB
    # 12/1TB
    # 12GB/1TB
    # 16GB/512GB
    # --------------------------------------------------------

    if not ram or not storage:

        title_match = re.search(
            r"\b"
            r"([0-9]+)"
            r"\s*(?:GB)?"
            r"\s*/\s*"
            r"([0-9]+(?:[.,][0-9]+)?)"
            r"\s*(GB|TB|T)"
            r"\b",
            title,
            re.IGNORECASE
        )

        if title_match:

            title_ram = (
                title_match.group(1)
                + " GB"
            )

            title_storage = (
                title_match.group(2)
                + " "
                + title_match.group(3).upper()
            )

            if not ram:

                ram = title_ram

            if not storage:

                storage = title_storage

    # --------------------------------------------------------
    # Additional fallback:
    #
    # Search card text for memory combinations
    #
    # Examples:
    # 12 GB / 1 TB
    # 12GB/512GB
    # --------------------------------------------------------

    if not ram or not storage:

        memory_match = re.search(
            r"\b"
            r"([0-9]+)"
            r"\s*(?:GB)?"
            r"\s*/\s*"
            r"([0-9]+(?:[.,][0-9]+)?)"
            r"\s*(GB|TB|T)"
            r"\b",
            card_text,
            re.IGNORECASE
        )

        if memory_match:

            memory_ram = (
                memory_match.group(1)
                + " GB"
            )

            memory_storage = (
                memory_match.group(2)
                + " "
                + memory_match.group(3).upper()
            )

            if not ram:

                ram = memory_ram

            if not storage:

                storage = memory_storage

    return ram, storage


# ============================================================
# PRICE EXTRACTION
# ============================================================

def extract_price(card):

    # --------------------------------------------------------
    # Main X-KOM price selector
    # --------------------------------------------------------

    price_element = card.locator(
        '[data-name="productPrice"] '
        'span[aria-label^="Cena:"]'
    ).first

    if price_element.count() > 0:

        aria_label = price_element.get_attribute(
            "aria-label"
        )

        price = clean_price(
            aria_label
        )

        if price is not None:
            return price

    # --------------------------------------------------------
    # Fallback: any aria-label containing Cena
    # --------------------------------------------------------

    price_element = card.locator(
        'span[aria-label*="Cena"]'
    ).first

    if price_element.count() > 0:

        aria_label = price_element.get_attribute(
            "aria-label"
        )

        price = clean_price(
            aria_label
        )

        if price is not None:
            return price

    # --------------------------------------------------------
    # Final fallback: card text
    # --------------------------------------------------------

    card_text = (
        card
        .inner_text()
        .strip()
    )

    # Look for a price followed by zł
    match = re.search(
        r"\d{1,3}(?:[\s\u00a0\u202f]\d{3})*(?:[,.]\d{1,2})?\s*zł",
        card_text,
        re.IGNORECASE
    )

    if match:

        return clean_price(
            match.group(0)
        )

    return None


# ============================================================
# AVAILABILITY
# ============================================================

def get_availability(card_text):

    return matching.classify_availability(card_text)


# ============================================================
# STORAGE NORMALIZATION
# ============================================================

def normalize_storage_to_gb(value):

    if value is None:
        return None

    text = str(value).lower().strip()

    # Remove spaces
    text = re.sub(r"\s+", "", text)

    # --------------------------------------------------------
    # TB / T -> GB
    # --------------------------------------------------------

    tb_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(tb|t)\b",
        str(value).lower()
    )

    if tb_match:

        number = float(
            tb_match.group(1).replace(",", ".")
        )

        return str(
            int(number * 1000)
        )

    # --------------------------------------------------------
    # GB
    # --------------------------------------------------------

    gb_match = re.search(
        r"(\d+)\s*gb\b",
        str(value).lower()
    )

    if gb_match:

        return gb_match.group(1)

    # --------------------------------------------------------
    # Plain number
    # --------------------------------------------------------

    number_match = re.search(
        r"\d+",
        text
    )

    if number_match:

        return number_match.group()

    return None

# ============================================================
# PRODUCTS
# ============================================================

def get_products(page, product):

    results = []

    print(
        "Waiting for X-kom products..."
    )

    # --------------------------------------------------------
    # Product cards
    # --------------------------------------------------------

    cards = page.locator(
        'div[data-name="productCard"]'
    )

    cards.first.wait_for(
        state="visible",
        timeout=30000
    )

    print(
        "X-kom product cards:",
        cards.count()
    )

    # --------------------------------------------------------
    # Target RAM / Storage
    # --------------------------------------------------------

    target_ram = re.sub(
        r"\D",
        "",
        str(product["ram"])
    )

    target_storage = normalize_storage_to_gb(
        product["storage"]
    )

    print(
        "Target RAM:",
        target_ram
    )

    print(
        "Target Storage:",
        target_storage,
        "GB"
    )

    print(
        "Target Product:",
        product["name"]
    )

    # --------------------------------------------------------
    # Track matching configuration
    # --------------------------------------------------------

    product_found = False

    # --------------------------------------------------------
    # Process cards
    # --------------------------------------------------------

    for i in range(cards.count()):

        card = cards.nth(i)

        try:

            # ------------------------------------------------
            # Product title
            # ------------------------------------------------

            title_element = card.locator(
                "h3"
            ).first

            if title_element.count() == 0:

                continue

            title = (
                title_element
                .inner_text()
                .strip()
            )

            print()
            print("=" * 60)
            print(
                "X-KOM PRODUCT",
                i
            )
            print("=" * 60)

            print(
                "TITLE:",
                title
            )

            # ------------------------------------------------
            # Product matching
            # ------------------------------------------------

            if not matches_product(
                title,
                product
            ):

                continue

            # ------------------------------------------------
            # Card text
            # ------------------------------------------------

            card_text = (
                card
                .inner_text()
                .strip()
            )

            # ------------------------------------------------
            # RAM / Storage
            # ------------------------------------------------

            ram, storage = extract_ram_storage(
                title,
                card_text
            )

            print(
                "RAM:",
                ram
            )

            print(
                "STORAGE:",
                storage
            )

            if not ram or not storage:

                print(
                    "RAM / Storage not found."
                )

                continue

            # ------------------------------------------------
            # Normalize RAM / Storage
            # ------------------------------------------------

            actual_ram = re.sub(
                r"\D",
                "",
                str(ram)
            )

            actual_storage = normalize_storage_to_gb(
                storage
            )

            print(
                "ACTUAL RAM:",
                actual_ram
            )

            print(
                "ACTUAL STORAGE:",
                actual_storage,
                "GB"
            )

            # ------------------------------------------------
            # Match RAM / Storage
            # ------------------------------------------------

            if actual_ram != target_ram:

                print(
                    "RAM mismatch."
                )

                continue

            if actual_storage != target_storage:

                print(
                    "Storage mismatch."
                )

                continue

            print(
                "RAM / STORAGE MATCH: YES"
            )

            # ------------------------------------------------
            # Matching configuration found
            # ------------------------------------------------

            product_found = True

            # ------------------------------------------------
            # COLOR
            # ------------------------------------------------

            color = get_color(
                title
            )

            print(
                "COLOR:",
                color
            )

            # ------------------------------------------------
            # AVAILABILITY
            # ------------------------------------------------

            availability = get_availability(
                card_text
            )

            print(
                "AVAILABILITY:",
                availability
            )

            # ------------------------------------------------
            # PRICE
            # ------------------------------------------------

            price = extract_price(
                card
            )

            print(
                "PRICE:",
                price
            )

            # ------------------------------------------------
            # Valid price fallback
            # ------------------------------------------------

            if (
                availability == "Unknown"
                and price is not None
            ):

                availability = "Available"

                print(
                    "AVAILABILITY updated to: Available "
                    "(valid price found)"
                )

            # ------------------------------------------------
            # SAVE RESULT
            # ------------------------------------------------

            result = {

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
            }

            print(
                "RESULT:",
                result
            )

            results.append(
                result
            )

        except Exception as e:

            print(
                "ERROR PROCESSING X-KOM CARD:",
                i,
                str(e)
            )

            continue

    # ========================================================
    # PRODUCT NOT FOUND
    # ========================================================

    if not product_found:

        print()
        print("=" * 60)
        print(
            "X-KOM: TARGET PRODUCT/CONFIGURATION NOT FOUND"
        )
        print("=" * 60)

        # Better display storage
        display_storage = normalize_storage_to_gb(
            product["storage"]
        )

        if display_storage == "1000":

            display_storage = "1 TB"

        else:

            display_storage = (
                f"{display_storage} GB"
            )

        results.append({

            "product_name":
                product["name"],

            "variant":
                "Unknown",

            "ram":
                f"{target_ram} GB",

            "storage":
                display_storage,

            "price":
                None,

            "availability":
                "Unavailable"
        })

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print(
        "X-KOM RESULTS:",
        len(results)
    )
    print("=" * 60)

    for result in results:

        print(result)

    return results


# ============================================================
# UNIFIED SCRAPER INTERFACE
# ============================================================

def get_price(page, product):

    return get_products(
        page,
        product
    )