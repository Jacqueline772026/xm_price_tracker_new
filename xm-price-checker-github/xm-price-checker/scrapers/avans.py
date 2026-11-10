import re

try:
    from . import matching      # imported as scrapers.<site> (normal case)
except ImportError:             # run as a plain script
    import matching


print(
    "AVANS MODULE PATH:",
    __file__
)


# ============================================================
# PRICE
# ============================================================

def clean_price(text):

    if not text:
        return None

    # Prefer Polish price patterns containing zł
    matches = re.findall(
        r"(\d[\d\s]*[,.]\d{2})\s*zł",
        text,
        re.IGNORECASE
    )

    if matches:

        value = (
            matches[-1]
            .replace(" ", "")
            .replace(",", ".")
        )

        try:
            return float(value)

        except ValueError:
            pass

    # --------------------------------------------------------
    # Split price format
    #
    # 399
    # 00
    #
    # --------------------------------------------------------

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for i, line in enumerate(lines):

        if re.fullmatch(
            r"\d{1,5}",
            line
        ):

            if i + 1 < len(lines):

                decimal = lines[i + 1]

                if re.fullmatch(
                    r"\d{2}",
                    decimal
                ):

                    try:

                        value = float(
                            f"{line}.{decimal}"
                        )

                        if value >= 50:

                            return value

                    except ValueError:

                        pass

    return None


# ============================================================
# COLOR
# ============================================================

def _get_color_base(title):

    title_lower = title.lower()

    # --------------------------------------------------------
    # Blue
    # --------------------------------------------------------
    if (
        "niebieski" in title_lower
        or "blue" in title_lower
    ):
        return "Blue"

    # --------------------------------------------------------
    # Black
    # --------------------------------------------------------
    elif (
        "czarny" in title_lower
        or "black" in title_lower
    ):
        return "Black"

    # --------------------------------------------------------
    # Green
    # --------------------------------------------------------
    elif (
        "zielony" in title_lower
        or "green" in title_lower
    ):
        return "Green"

    # --------------------------------------------------------
    # White
    # --------------------------------------------------------
    elif (
        "biały" in title_lower
        or "white" in title_lower
    ):
        return "White"

    # --------------------------------------------------------
    # Grey
    # --------------------------------------------------------
    elif (
        "szary" in title_lower
        or "grey" in title_lower
        or "gray" in title_lower
    ):
        return "Grey"

    # --------------------------------------------------------
    # Silver
    # --------------------------------------------------------
    elif (
        "srebrny" in title_lower
        or "silver" in title_lower
    ):
        return "Silver"

    # --------------------------------------------------------
    # orange
    # --------------------------------------------------------
    elif (
        "Pomarańczowy" in title_lower
        or "orange" in title_lower
    ):
        return "Orange"

    # --------------------------------------------------------
    # Purple
    # --------------------------------------------------------
    elif (
        "fioletowy" in title_lower
        or "purple" in title_lower
    ):
        return "Purple"

    # --------------------------------------------------------
    # Pink
    # --------------------------------------------------------
    elif (
        "różowy" in title_lower
        or "pink" in title_lower
    ):
        return "Pink"

    # --------------------------------------------------------
    # Titanium
    # --------------------------------------------------------
    elif (
        "tytanowy" in title_lower
        or "titanium" in title_lower
    ):
        return "Titanium"

    # --------------------------------------------------------
    # Brown
    # --------------------------------------------------------
    elif (
        "brązowy" in title_lower
        or "brown" in title_lower
        or "mocha" in title_lower
    ):
        return "Brown"

    # --------------------------------------------------------
    # Unknown
    # --------------------------------------------------------
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

def match_product(title, target_name):

    """
    Strict product matching.

    Important distinctions:

    - Redmi Note 15 != Redmi Note 15 Pro
    - Redmi Note 15 Pro != Redmi Note 15 Pro+
    - Redmi Note 15 != Redmi Note 15 5G

    - Xiaomi 17 != Xiaomi 17T
    - Xiaomi 17T != Xiaomi 17T Pro
    - Xiaomi 17 != Xiaomi 17 Ultra
    """

    if not title or not target_name:
        return False

    # --------------------------------------------------
    # NORMALIZE TEXT
    # --------------------------------------------------

    def normalize(text):

        text = str(text).lower()

        # Normalize plus symbols
        text = text.replace("＋", "+")
        text = text.replace(" pro +", " pro+")

        # Remove common website / brand words
        text = re.sub(
            r"\bsmartfon\b",
            " ",
            text
        )

        text = re.sub(
            r"\bxiaomi\b",
            " ",
            text
        )

        # Normalize punctuation
        text = re.sub(
            r"[\"“”]",
            " ",
            text
        )

        # Keep + because Pro+ is important
        text = re.sub(
            r"[^a-z0-9+]+",
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


    title_norm = normalize(title)
    target_norm = normalize(target_name)

    print(
        "NORMALIZED TITLE:",
        title_norm
    )

    print(
        "NORMALIZED TARGET:",
        target_norm
    )

    # --------------------------------------------------
    # SPECIAL STRICT MATCHING FOR REDMI NOTE SERIES
    # --------------------------------------------------

    if "redmi note" in target_norm:

        target_model_match = re.search(
            r"\bredmi note (\d+)\b",
            target_norm
        )

        title_model_match = re.search(
            r"\bredmi note (\d+)\b",
            title_norm
        )

        if (
            not target_model_match
            or
            not title_model_match
        ):
            return False

        target_model = (
            target_model_match.group(1)
        )

        title_model = (
            title_model_match.group(1)
        )

        # Different generation
        if target_model != title_model:

            print(
                "Product mismatch: different Redmi Note generation."
            )

            return False

        # --------------------------------------------------
        # Detect variant
        # --------------------------------------------------

        def get_variant(text):

            if re.search(
                r"\bpro\+",
                text
            ):
                return "pro+"

            if re.search(
                r"\bpro\b",
                text
            ):
                return "pro"

            return "base"


        target_variant = get_variant(
            target_norm
        )

        title_variant = get_variant(
            title_norm
        )

        if target_variant != title_variant:

            print(
                "Product mismatch: different Redmi Note variant."
            )

            return False

        # --------------------------------------------------
        # Detect 5G
        # --------------------------------------------------

        target_has_5g = bool(
            re.search(
                r"\b5g\b",
                target_norm
            )
        )

        title_has_5g = bool(
            re.search(
                r"\b5g\b",
                title_norm
            )
        )

        if target_has_5g != title_has_5g:

            print(
                "Product mismatch: different 5G version."
            )

            return False

        return True


    # ==================================================
    # STRICT TOKEN MATCHING FOR ALL OTHER PRODUCTS
    # ==================================================

    target_tokens = target_norm.split()
    title_tokens = title_norm.split()

    if not target_tokens:

        return False

    # --------------------------------------------------
    # Find the exact target token sequence
    #
    # Example:
    #
    # Target:
    # 17t
    #
    # Title:
    # 17t pro
    #
    # The sequence is found, but "pro" is an additional
    # model-version word, so reject it.
    # --------------------------------------------------

    model_modifiers = {
        "pro",
        "pro+",
        "ultra",
        "max",
        "lite",
        "plus",
    }

    for start in range(

        len(title_tokens)
        - len(target_tokens)
        + 1

    ):

        end = start + len(target_tokens)

        if (
            title_tokens[start:end]
            != target_tokens
        ):

            continue

        # ------------------------------------------------
        # If the title continues with another model
        # modifier, it is NOT the same product.
        # ------------------------------------------------

        if end < len(title_tokens):

            next_token = title_tokens[end]

            if next_token in model_modifiers:

                print(
                    "Product mismatch: additional "
                    f"model version '{next_token}'."
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

def normalize_storage_value(value):

    if value is None:

        return None

    text = (
        str(value)
        .upper()
        .replace(" ", "")
        .replace("\u00A0", "")
    )

    # --------------------------------------------------------
    # TB / T
    #
    # Important:
    #
    # Retail websites may describe the same storage as:
    #
    # 1TB
    # 1 TB
    # 1T
    # 1000GB
    #
    # For product matching, use decimal retail storage:
    #
    # 1TB = 1000GB
    # --------------------------------------------------------

    tb_match = re.fullmatch(
        r"(\d+(?:[.,]\d+)?)T(?:B)?",
        text
    )

    if tb_match:

        try:

            tb_value = float(
                tb_match.group(1).replace(",", ".")
            )

            return str(
                int(tb_value * 1000)
            )

        except ValueError:

            return None

    # --------------------------------------------------------
    # GB
    #
    # Examples:
    #
    # 512
    # 512GB
    # 1000GB
    # --------------------------------------------------------

    gb_match = re.search(
        r"(\d+)",
        text
    )

    if not gb_match:

        return None

    return gb_match.group(1)

# ============================================================
# RAM / STORAGE
# ============================================================

def get_ram_storage(text):

    # --------------------------------------------------------
    # Avans formats:
    #
    # Pamięć RAM/Wewnętrzna: 4 GB / 64 GB
    # Pamięć RAM/Wewnętrzna: 12 GB / 512 GB
    # Pamięć RAM/Wewnętrzna: 12 GB / 1 TB
    # --------------------------------------------------------

    match = re.search(
        r"Pamięć\s+RAM/Wewnętrzna:\s*"
        r"(\d+)\s*GB\s*/\s*"
        r"(\d+)\s*(GB|TB)",
        text,
        re.IGNORECASE
    )

    if not match:

        return None, None

    ram_value = match.group(1)

    storage_value = match.group(2)

    storage_unit = (
        match.group(3)
        .upper()
    )

    ram = (
        ram_value
        + " GB"
    )

    storage = (
        storage_value
        + " "
        + storage_unit
    )

    return ram, storage

def normalize_ram_value(value):

    if value is None:

        return None

    text = str(value).upper()

    match = re.search(
        r"(\d+)",
        text
    )

    if not match:

        return None

    return match.group(1)


# ------------------------------------------------------------
# Storage Normalization
# ------------------------------------------------------------

def normalize_storage(value):

    if value is None:
        return None

    text = (
        str(value)
        .upper()
        .replace(" ", "")
        .replace("\u00a0", "")
    )

    # --------------------------------------------------------
    # TB
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:[.,]\d+)?)TB",
        text
    )

    if match:

        number = float(
            match.group(1).replace(",", ".")
        )

        # Xiaomi/retailer storage convention:
        # 1 TB = 1000 GB
        return str(
            int(number * 1000)
        )

    # --------------------------------------------------------
    # GB
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:[.,]\d+)?)GB",
        text
    )

    if match:

        number = float(
            match.group(1).replace(",", ".")
        )

        return str(
            int(number)
        )

    # --------------------------------------------------------
    # Plain number fallback
    # --------------------------------------------------------

    digits = re.sub(
        r"\D",
        "",
        text
    )

    return digits if digits else None

# ============================================================
# AVAILABILITY
# ============================================================

def get_availability(text):

    return matching.classify_availability(text)


# ============================================================
# GET PRODUCTS
# ============================================================

def get_products(page, product):

    results = []

    print(
        "Waiting for Avans products..."
    )

    # --------------------------------------------------------
    # Find product titles
    # --------------------------------------------------------

    titles = page.locator(
        "h2"
    )

    count = titles.count()

    print(
        "Total Avans H2:",
        count
    )

    # ========================================================
    # PROCESS PRODUCTS
    # ========================================================

    for i in range(count):

        title_element = titles.nth(i)

        try:

            title = (
                title_element
                .inner_text()
                .strip()
            )

        except Exception:

            continue

        # ----------------------------------------------------
        # Match target product
        # ----------------------------------------------------

        if not match_product(
            title,
            product["name"]
        ):

            print(
                "Product name mismatch."
            )

            continue

        print(
            "PRODUCT NAME MATCH: YES"
        )

        # ----------------------------------------------------
        # Only actual smartphone products
        # ----------------------------------------------------

        if "smartfon" not in title.lower():

            print(
                "Skipping: not a smartphone product."
            )

            continue

        print()
        print(
            "=" * 60
        )

        print(
            f"AVANS PRODUCT {i}"
        )

        print(
            "=" * 60
        )

        print(
            "TITLE:",
            title
        )

        # ----------------------------------------------------
        # Find product container
        # ----------------------------------------------------

        try:

            container = (
                title_element
                .locator(
                    "xpath=ancestor::div[contains(@class,'offer-box')]"
                )
                .first
            )

            if container.count() == 0:

                print(
                    "Could not find offer-box."
                )

                continue

        except Exception as e:

            print(
                "Container error:",
                e
            )

            continue

        # ----------------------------------------------------
        # Extract complete product text
        # ----------------------------------------------------

        try:

            text = (
                container
                .inner_text()
                .strip()
            )

        except Exception as e:

            print(
                "Could not read product container:",
                e
            )

            continue

        # ----------------------------------------------------
        # DEBUG CARD TEXT
        # ----------------------------------------------------

        print()
        print(
            "AVANS FULL CARD TEXT:"
        )

        print(
            "-" * 60
        )

        print(
            text
        )

        print(
            "-" * 60
        )

        # ----------------------------------------------------
        # RAM / STORAGE
        # ----------------------------------------------------

        ram, storage = get_ram_storage(
            text
        )

        print(
            "RAM:",
            ram
        )

        print(
            "STORAGE:",
            storage
        )

        # ----------------------------------------------------
        # STRICT RAM / STORAGE MATCHING
        # ----------------------------------------------------

        target_ram = normalize_ram_value(
            product.get("ram")
        )

        target_storage = normalize_storage_value(
            product.get("storage")
        )

        actual_ram = normalize_ram_value(
            ram
        )

        actual_storage = normalize_storage_value(
            storage
        )

        print(
            "TARGET RAM:",
            target_ram
        )

        print(
            "TARGET STORAGE:",
            target_storage
        )

        print(
            "ACTUAL RAM:",
            actual_ram
        )

        print(
            "ACTUAL STORAGE:",
            actual_storage
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # If we cannot extract the complete configuration,
        # do not accept the product.
        #
        # This prevents:
        #
        # 12/512
        #
        # from accidentally matching:
        #
        # 12/1TB
        # ----------------------------------------------------

        if (
            actual_ram is None
            or
            actual_storage is None
        ):

            print(
                "Skipping: could not extract complete "
                "RAM/storage configuration."
            )

            continue

        # ----------------------------------------------------
        # RAM must match exactly
        # ----------------------------------------------------

        if actual_ram != target_ram:

            print(
                "Skipping: RAM mismatch."
            )

            continue

        # ----------------------------------------------------
        # Storage must match exactly
        # ----------------------------------------------------

        if actual_storage != target_storage:

            print(
                "Skipping: storage mismatch."
            )

            continue

        print(
            "RAM / STORAGE MATCH: YES"
        )

        # ----------------------------------------------------
        # COLOR
        # ----------------------------------------------------

        color = get_color(
            title
        )

        print(
            "COLOR:",
            color
        )

        # ----------------------------------------------------
        # AVAILABILITY
        # ----------------------------------------------------

        availability = get_availability(
            text
        )

        print(
            "AVAILABILITY:",
            availability
        )

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price = clean_price(
            text
        )

        print(
            "PRICE:",
            price
        )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

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

    # ========================================================
    # PRODUCT NOT FOUND
    # ========================================================

    if not results:

        print()

        print(
            "=" * 60
        )

        print(
            "TARGET PRODUCT NOT FOUND"
        )

        print(
            "Returning Unavailable."
        )

        print(
            "=" * 60
        )

        results.append(

            {
                "product_name":
                    product["name"],

                "variant":
                    "Unknown",

                "ram":
                    (
                        f'{product.get("ram", "")} GB'
                        if product.get("ram")
                        else "Unknown"
                    ),

                "storage":
                    (
                        f'{product.get("storage", "")}'
                        if product.get("storage")
                        else "Unknown"
                    ),

                "price":
                    None,

                "availability":
                    "Unavailable"
            }
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print(
        "=" * 60
    )

    print(
        "AVANS RESULTS:",
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