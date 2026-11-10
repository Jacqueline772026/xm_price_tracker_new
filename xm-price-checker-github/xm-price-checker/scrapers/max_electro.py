import re

try:
    from . import matching      # imported as scrapers.<site> (normal case)
except ImportError:             # run as a plain script
    import matching


# ------------------------------------------------------------
# Price
# ------------------------------------------------------------

def clean_price(text):

    if not text:
        return None

    text = (
        str(text)
        .replace("\u00a0", " ")
        .strip()
    )

    # Remove currency text
    text = re.sub(
        r"\b(zł|pln)\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.strip()

    # --------------------------------------------------------
    # Polish / European format
    #
    # Examples:
    #
    # 899,99
    # 899.99
    # 1 899,99
    # 1.899,99
    # --------------------------------------------------------

    match = re.search(
        r"(\d[\d\s.]*[,.]\d{1,2})",
        text
    )

    if match:

        value = (
            match.group(1)
            .replace(" ", "")
        )

        # 1.899,99 -> 1899.99
        if "," in value and "." in value:

            if value.rfind(",") > value.rfind("."):

                value = (
                    value
                    .replace(".", "")
                    .replace(",", ".")
                )

            else:

                value = value.replace(",", "")

        # 899,99 -> 899.99
        elif "," in value:

            value = value.replace(",", ".")

        try:

            price = float(value)

            # Phone prices below 10 PLN are almost certainly
            # promotional text or an unrelated price.
            if price < 10:

                return None

            return price

        except ValueError:

            return None

    # --------------------------------------------------------
    # Integer price
    #
    # Example:
    #
    # 899
    # --------------------------------------------------------

    match = re.fullmatch(
        r"\s*(\d[\d\s]*)\s*",
        text
    )

    if match:

        value = (
            match.group(1)
            .replace(" ", "")
        )

        try:

            price = float(value)

            if price < 10:

                return None

            return price

        except ValueError:

            return None

    return None

# ------------------------------------------------------------
# Color
# ------------------------------------------------------------

def _get_color_base(title):

    title_lower = (
        title
        .lower()
        .replace("\u00a0", " ")
    )

    # --------------------------------------------------------
    # English / marketing colors
    # --------------------------------------------------------

    if "glacier blue" in title_lower:
        return "Blue"

    elif "ocean blue" in title_lower:
        return "Blue"

    elif "ocean teal" in title_lower:
        return "Green"

    elif "midnight black" in title_lower:
        return "Black"

    elif "forest green" in title_lower:
        return "Green"

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

    elif re.search(r"\bgrey\b", title_lower):
        return "Grey"

    elif re.search(r"\bgray\b", title_lower):
        return "Grey"

    elif re.search(r"\bsilver\b", title_lower):
        return "Silver"

    elif re.search(r"\bgold\b", title_lower):
        return "Gold"

    elif re.search(r"\bpurple\b", title_lower):
        return "Purple"

    elif re.search(r"\bpink\b", title_lower):
        return "Pink"
    
    elif re.search(r"\bbrown\b", title_lower):
        return "Brown"

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


# ------------------------------------------------------------
# Product Matching
# ------------------------------------------------------------

# ------------------------------------------------------------
# Product Matching
# ------------------------------------------------------------


def get_color(title):

    """Scraper colour list first, shared wide list as fallback."""

    colour = _get_color_base(title)

    if colour == "Unknown":
        colour = matching.detect_colour(title)

    return colour


def normalize_product_text(text):

    text = (
        str(text)
        .lower()
        .replace("\u00a0", " ")
        .strip()
    )

    # Normalize different ways Pro+ may appear
    text = re.sub(
        r"\bpro\s*\+",
        "pro+",
        text
    )

    # Separate common punctuation
    text = re.sub(
        r"[/(),;:_\-]+",
        " ",
        text
    )

    # Keep letters, numbers, spaces and +
    text = re.sub(
        r"[^a-z0-9ąćęłńóśźż+\s]",
        " ",
        text
    )

    # Normalize spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def matches_product(title, product):

    # --------------------------------------------------------
    # Normalize title and target product name
    # --------------------------------------------------------

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
    #
    # Target with 5G must match title with 5G.
    # Target without 5G must not match title with 5G.
    #
    # Max Elektro is NOT KTR, so we do not ignore 5G here.
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
    # Remove 5G AFTER checking it
    #
    # This allows us to compare the actual model name while
    # still requiring both products to have the same 5G status.
    # --------------------------------------------------------

    target_core = re.sub(
        r"\b5g\b",
        "",
        target_normalized
    )

    title_core = re.sub(
        r"\b5g\b",
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

    if not target_tokens:

        return False

    # --------------------------------------------------------
    # Product version words
    #
    # These indicate that the title may be a different model.
    # --------------------------------------------------------

    product_modifiers = {
        "pro",
        "pro+",
        "ultra",
        "max",
        "lite",
        "plus",
    }

    # --------------------------------------------------------
    # Find exact product-name token sequence
    #
    # Examples:
    #
    # Xiaomi 17
    # ≠ Xiaomi 17T
    #
    # Xiaomi 17T
    # ≠ Xiaomi 17T Pro
    #
    # Redmi Note 15
    # ≠ Redmi Note 15 Pro
    #
    # Redmi Note 15 Pro
    # ≠ Redmi Note 15 Pro+
    # --------------------------------------------------------

    for start in range(
        len(title_tokens)
        - len(target_tokens)
        + 1
    ):

        end = (
            start
            + len(target_tokens)
        )

        candidate = title_tokens[start:end]

        if candidate != target_tokens:

            continue

        # ----------------------------------------------------
        # Check what comes immediately after the product name
        # ----------------------------------------------------

        if end < len(title_tokens):

            next_token = title_tokens[end]

            if next_token in product_modifiers:

                print(
                    "Product mismatch: website title has "
                    f"additional model version '{next_token}'."
                )

                continue

        print(
            "Product name MATCH."
        )

        return True

    print(
        "Product name mismatch."
    )

    return False


def matches_product(title, product):

    # --------------------------------------------------------
    # Normalize title and target product name
    # --------------------------------------------------------

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
    # 5G matching
    #
    # Target with 5G must match a title with 5G.
    # Target without 5G must not match a title with 5G.
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
    # Remove 5G for core product-name comparison
    # --------------------------------------------------------

    target_core = re.sub(
        r"\b5g\b",
        "",
        target_normalized
    )

    title_core = re.sub(
        r"\b5g\b",
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
    # Find exact sequence of product-name tokens
    #
    # Example:
    #
    # Target:
    # Redmi Note 15
    #
    # Will find:
    # ["redmi", "note", "15"]
    #
    # but then we check what comes immediately after it.
    # --------------------------------------------------------

    match_found = False

    for start in range(
        len(title_tokens) - len(target_tokens) + 1
    ):

        end = start + len(target_tokens)

        if (
            title_tokens[start:end]
            != target_tokens
        ):
            continue

        # ----------------------------------------------------
        # Check whether the website product continues with
        # another product-version word.
        #
        # This prevents:
        #
        # Redmi Note 15
        # matching
        # Redmi Note 15 Pro
        #
        # ----------------------------------------------------

        if end < len(title_tokens):

            next_token = title_tokens[end]

            product_modifiers = {
                "pro",
                "pro+",
                "ultra",
                "max",
                "lite",
                "plus",
            }

            if next_token in product_modifiers:

                print(
                    "Product mismatch: website title has "
                    f"additional model version '{next_token}'."
                )

                continue

        # ----------------------------------------------------
        # Exact product model found
        # ----------------------------------------------------

        match_found = True
        break

    if not match_found:

        print(
            "Product name mismatch."
        )

        return False

    # --------------------------------------------------------
    # Product matches
    # --------------------------------------------------------

    return True

# ------------------------------------------------------------
# Storage Normalization
# ------------------------------------------------------------

def normalize_storage_to_gb(value):

    if value is None:

        return None

    text = (
        str(value)
        .lower()
        .replace("\u00a0", " ")
        .replace(" ", "")
        .strip()
    )

    # --------------------------------------------------------
    # TB / T
    #
    # 1TB
    # 1T
    # 1 TB
    # --------------------------------------------------------

    tb_match = re.fullmatch(
        r"(\d+(?:[.,]\d+)?)tb?",
        text
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
    #
    # 512GB
    # 512
    # --------------------------------------------------------

    gb_match = re.search(
        r"(\d+)",
        text
    )

    if gb_match:

        return gb_match.group(1)

    return None


# ------------------------------------------------------------
# Price Extraction
# ------------------------------------------------------------

def extract_price(card):

    card_text = (
        card
        .inner_text()
        .replace("\u00a0", " ")
        .strip()
    )

    card_text_lower = card_text.lower()

    # --------------------------------------------------------
    # Unavailable products
    # --------------------------------------------------------

    if (
        "produkt niedostępny" in card_text_lower
        or
        "brak w magazynie" in card_text_lower
        or
        "chwilowo niedostępny" in card_text_lower
    ):

        return None

    # --------------------------------------------------------
    # Split card text into clean lines
    # --------------------------------------------------------

    lines = []

    for line in card_text.splitlines():

        line = line.strip()

        if line:

            lines.append(line)

    # --------------------------------------------------------
    # MAX ELEKTRO MAIN PRICE - split format
    #
    # Example:
    #
    # 899
    # 00
    # zł
    #
    # This is checked FIRST because the card may also contain
    # unrelated promotional text such as:
    #
    # "Orange za 1 zł"
    # --------------------------------------------------------

    for i in range(len(lines) - 2):

        whole = lines[i]
        decimal = lines[i + 1]
        currency = lines[i + 2]

        # Whole price:
        #
        # 899
        # 1899
        # 1 899
        #
        whole_match = re.fullmatch(
            r"\d[\d\s]*",
            whole
        )

        # Decimal:
        #
        # 00
        # 99
        #
        decimal_match = re.fullmatch(
            r"\d{2}",
            decimal
        )

        # Currency:
        #
        # zł
        #
        currency_match = re.fullmatch(
            r"zł",
            currency,
            re.IGNORECASE
        )

        if (
            whole_match
            and decimal_match
            and currency_match
        ):

            value = (
                whole
                .replace(" ", "")
                + "."
                + decimal
            )

            try:

                price = float(value)

                # Ignore suspicious promotional prices
                if price >= 10:

                    return price

            except ValueError:

                pass

    # --------------------------------------------------------
    # Normal decimal price
    #
    # Examples:
    #
    # 899,99 zł
    # 899.99 zł
    # 1 899,99 zł
    # --------------------------------------------------------

    for line in lines:

        match = re.search(
            r"(\d[\d\s.]*[,.]\d{1,2})\s*zł",
            line,
            re.IGNORECASE
        )

        if match:

            price = clean_price(
                match.group(1)
            )

            if price is not None:

                return price

    # --------------------------------------------------------
    # Integer price followed directly by zł
    #
    # Example:
    #
    # 899 zł
    #
    # We deliberately require at least 2 digits to avoid
    # promotional text such as "za 1 zł".
    # --------------------------------------------------------

    for line in lines:

        match = re.search(
            r"\b(\d{2,}[\d\s]*)\s*zł\b",
            line,
            re.IGNORECASE
        )

        if match:

            price = clean_price(
                match.group(1)
            )

            if price is not None:

                return price

    # --------------------------------------------------------
    # Price not found
    # --------------------------------------------------------

    return None


# ------------------------------------------------------------
# Products
# ------------------------------------------------------------

def get_products(page, product):

    results = []

    print(
        "Waiting for Max Elektro products..."
    )

    # --------------------------------------------------------
    # Product cards
    # --------------------------------------------------------

    cards = page.locator(
        "div.product_cart-item"
    )

    print(
        "Max Elektro product cards:",
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
        "TARGET RAM:",
        target_ram
    )

    print(
        "TARGET STORAGE:",
        target_storage,
        "GB"
    )

    # --------------------------------------------------------
    # Track whether matching product was found
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
                "MAX ELEKTRO CARD",
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

            print(
                "PRODUCT NAME MATCH: YES"
            )

            # ------------------------------------------------
            # Card text
            # ------------------------------------------------

            card_text = (
                card
                .inner_text()
                .strip()
            )

            print()
            print(
                "CARD TEXT:"
            )
            print("-" * 60)
            print(
                card_text
            )
            print("-" * 60)

            # ------------------------------------------------
            # RAM
            # ------------------------------------------------

            ram_match = re.search(
                r"Pamięć RAM\s*\(GB\)\s*([0-9]+)",
                card_text,
                re.IGNORECASE
            )

            if not ram_match:

                print(
                    "RAM not found."
                )

                continue

            ram = (
                ram_match.group(1)
                + " GB"
            )

            print(
                "RAM:",
                ram
            )

            # ------------------------------------------------
            # Storage
            #
            # Supports:
            #
            # 8/256GB
            # 12/512GB
            # 12/1TB
            # 12/1T
            # ------------------------------------------------

            storage_match = re.search(
                r"\d+\s*/\s*"
                r"(\d+(?:[.,]\d+)?)\s*"
                r"(GB|TB|T)\b",
                title,
                re.IGNORECASE
            )

            if not storage_match:

                print(
                    "STORAGE not found."
                )

                continue

            storage_number = (
                storage_match.group(1)
            )

            storage_unit = (
                storage_match.group(2)
                .upper()
            )

            storage_raw = (
                storage_number
                + storage_unit
            )

            storage_value = normalize_storage_to_gb(
                storage_raw
            )

            if storage_value is None:

                print(
                    "STORAGE could not be normalized."
                )

                continue

            storage = (
                storage_value
                + " GB"
            )

            print(
                "STORAGE RAW:",
                storage_raw
            )

            print(
                "STORAGE:",
                storage
            )

            # ------------------------------------------------
            # RAM / Storage matching
            # ------------------------------------------------

            ram_match_value = re.sub(
                r"\D",
                "",
                ram
            )

            storage_match_value = normalize_storage_to_gb(
                storage
            )

            print(
                "ACTUAL RAM:",
                ram_match_value
            )

            print(
                "ACTUAL STORAGE:",
                storage_match_value,
                "GB"
            )

            if ram_match_value != target_ram:

                print(
                    "Skipping: RAM mismatch."
                )

                continue

            if storage_match_value != target_storage:

                print(
                    "Skipping: storage mismatch."
                )

                continue

            print(
                "RAM / STORAGE MATCH: YES"
            )

            # ------------------------------------------------
            # Matching product found
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

            availability = matching.classify_availability(card_text)

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
            # RESULT
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

            # ------------------------------------------------
            # SAVE RESULT
            # ------------------------------------------------

            results.append(
                result
            )

        except Exception as e:

            print(
                "ERROR PROCESSING CARD:",
                i,
                str(e)
            )

            continue

    # ========================================================
    # NO MATCHING PRODUCT
    # ========================================================

    if not product_found:

        print()
        print("=" * 60)

        print(
            "MAX ELEKTRO: TARGET PRODUCT NOT FOUND"
        )

        print("=" * 60)

        print(
            "Product:",
            product["name"]
        )

        print(
            "RAM:",
            product["ram"]
        )

        print(
            "STORAGE:",
            product["storage"]
        )

        print(
            "Availability: Unavailable"
        )

        # Normalize fallback storage for display

        fallback_storage = normalize_storage_to_gb(
            product["storage"]
        )

        if fallback_storage:

            fallback_storage = (
                fallback_storage
                + " GB"
            )

        else:

            fallback_storage = str(
                product["storage"]
            )

        results.append({

            "product_name":
                product["name"],

            "variant":
                "Unknown",

            "ram":
                str(product["ram"])
                + " GB",

            "storage":
                fallback_storage,

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
        "MAX ELEKTRO RESULTS:",
        len(results)
    )

    print("=" * 60)

    for result in results:

        print(
            result
        )

    return results