import re

try:
    from . import matching      # imported as scrapers.<site> (normal case)
except ImportError:             # run as a plain script
    import matching


print(
    "NEONET MODULE PATH:",
    __file__
)


# ============================================================
# PRICE
# ============================================================

def clean_price(text):

    if not text:
        return None

    text = (
        str(text)
        .replace("\u00a0", " ")
        .strip()
    )

    # --------------------------------------------------------
    # Normal price
    #
    # Examples:
    #
    # 1 899.00 PLN
    # 1899,99 zł
    # 1899.00 zł
    # --------------------------------------------------------

    matches = re.findall(
        r"(\d[\d\s]*[,.]\d{2})\s*(?:PLN|zł)",
        text,
        re.IGNORECASE
    )

    if matches:

        # Usually the first real price with currency is the
        # current product price.
        value = (
            matches[0]
            .replace(" ", "")
            .replace(",", ".")
        )

        try:
            return float(value)

        except ValueError:
            pass

    # --------------------------------------------------------
    # Split price
    #
    # Example:
    #
    # 1 899
    # 00
    # PLN
    # --------------------------------------------------------

    match = re.search(
        r"(\d[\d\s]*)\s+(\d{2})\s*(?:PLN|zł)",
        text,
        re.IGNORECASE
    )

    if match:

        value = (
            match.group(1)
            .replace(" ", "")
            + "."
            + match.group(2)
        )

        try:
            return float(value)

        except ValueError:
            pass

    # --------------------------------------------------------
    # Integer price with currency
    #
    # Example:
    #
    # 1899 PLN
    # 899 zł
    # --------------------------------------------------------

    match = re.search(
        r"(\d[\d\s]*)\s*(?:PLN|zł)",
        text,
        re.IGNORECASE
    )

    if match:

        value = (
            match.group(1)
            .replace(" ", "")
        )

        try:
            return float(value)

        except ValueError:
            pass

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

    elif "midnight black" in title_lower:
        return "Black"

    elif "mocha brown" in title_lower:
        return "Brown"

    elif "forest green" in title_lower:
        return "Green"

    elif "aurora purple" in title_lower:
        return "Purple"

    elif "ocean teal" in title_lower:
        return "Green"

    # --------------------------------------------------------
    # English colors
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
    # Remove common punctuation
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
    # LTE matching
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
    # 5G matching
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
    # Special rule:
    #
    # Base Redmi Pad 2 must NOT match Redmi Pad 2 4G.
    #
    # This rule intentionally applies ONLY to the exact
    # product "Redmi Pad 2" so it will not affect other models.
    # --------------------------------------------------------

    if target_normalized == "redmi pad 2":

        title_has_4g = bool(
            re.search(
                r"\b4g\b",
                title_normalized
            )
        )

        if title_has_4g:

            print(
                "Product mismatch: Redmi Pad 2 4G version does not match."
            )

            return False

    # --------------------------------------------------------
    # Remove LTE and 5G for product-name comparison
    # --------------------------------------------------------

    target_core = re.sub(
        r"\b(?:5g|lte)\b",
        "",
        target_normalized
    )

    title_core = re.sub(
        r"\b(?:5g|lte)\b",
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
    # Find exact product token sequence
    # --------------------------------------------------------

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
        # Prevent base model matching Pro / Pro+ / Ultra etc.
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

# ============================================================
# STORAGE NORMALIZATION
# ============================================================

def normalize_storage_value(value):

    if value is None:
        return ""

    text = (
        str(value)
        .lower()
        .replace("\u00a0", " ")
        .strip()
    )

    # Remove spaces for easier matching
    compact = re.sub(
        r"\s+",
        "",
        text
    )

    # --------------------------------------------------------
    # TB / T formats
    #
    # Examples:
    #
    # 1T
    # 1TB
    # 1 TB
    # --------------------------------------------------------

    tb_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(tb|t)\b",
        text
    )

    if not tb_match:

        tb_match = re.search(
            r"(\d+(?:[.,]\d+)?)(tb|t)",
            compact
        )

    if tb_match:

        number = (
            tb_match
            .group(1)
            .replace(",", ".")
        )

        try:

            return str(
                int(
                    float(number) * 1000
                )
            )

        except ValueError:

            return ""

    # --------------------------------------------------------
    # GB formats
    #
    # Examples:
    #
    # 512
    # 512GB
    # 512 GB
    # --------------------------------------------------------

    gb_match = re.search(
        r"(\d+)",
        text
    )

    if gb_match:

        return gb_match.group(1)

    return ""

# ============================================================
# RAM / STORAGE
# ============================================================

# ============================================================
# RAM / STORAGE
# ============================================================

def get_configuration_from_title(title):

    title = str(title)

    # --------------------------------------------------------
    # Examples:
    #
    # 8/256 GB
    # 8/256GB
    # 4 / 128 GB
    # 12/1TB
    # 12 / 1 TB
    # --------------------------------------------------------

    match = re.search(
        r"(\d+)\s*/\s*(\d+(?:[.,]\d+)?)\s*(GB|TB|T)\b",
        title,
        re.IGNORECASE
    )

    if match:

        ram = match.group(1) + " GB"

        storage_number = match.group(2)

        storage_unit = (
            match.group(3)
            .upper()
        )

        if storage_unit in ("TB", "T"):

            try:

                storage = (
                    str(
                        int(
                            float(
                                storage_number.replace(",", ".")
                            ) * 1000
                        )
                    )
                    + " GB"
                )

            except ValueError:

                storage = "Unknown"

        else:

            storage = (
                storage_number
                + " GB"
            )

        return ram, storage

    return None, None


def get_ram(text):

    match = re.search(
        r"Pamięć\s+RAM:\s*(\d+)\s*GB",
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(1) + " GB"

    return "Unknown"


def get_storage(text):

    text = str(text)

    match = re.search(
        r"Pamięć\s+wbudowana:\s*"
        r"(\d+(?:[.,]\d+)?)\s*(GB|TB|T)\b",
        text,
        re.IGNORECASE
    )

    if match:

        number = match.group(1)

        unit = (
            match.group(2)
            .upper()
        )

        if unit in ("TB", "T"):

            try:

                return (
                    str(
                        int(
                            float(
                                number.replace(",", ".")
                            ) * 1000
                        )
                    )
                    + " GB"
                )

            except ValueError:

                return "Unknown"

        return number + " GB"

    return "Unknown"


# ============================================================
# AVAILABILITY
# ============================================================

def get_availability(text):

    return matching.classify_availability(text)


# ============================================================
# FIND PRODUCT CARD
# ============================================================

def find_product_card(heading):

    # --------------------------------------------------------
    # Move upwards from the H3.
    #
    # We want the smallest ancestor that looks like one
    # product card, rather than a large container containing
    # several products.
    # --------------------------------------------------------

    for level in range(1, 10):

        try:

            candidate = heading.locator(
                "xpath=" + "/.." * level
            )

            candidate_text = (
                candidate
                .inner_text()
                .strip()
            )

            if not candidate_text:
                continue

            candidate_text_lower = (
                candidate_text
                .lower()
                .replace("\u00a0", " ")
            )

            # ------------------------------------------------
            # Check how many H3 titles are inside.
            #
            # A real product card should normally contain only
            # one product title.
            # ------------------------------------------------

            h3_count = candidate.locator(
                "h3"
            ).count()

            if h3_count > 1:
                continue

            # ------------------------------------------------
            # Product card indicators
            # ------------------------------------------------

            indicators = [

                "pln",
                "zł",
                "dodaj do koszyka",
                "add to cart",
                "niedostępny",
                "dostępny",
                "free shipping",
                "price",

            ]

            if any(
                indicator in candidate_text_lower
                for indicator in indicators
            ):

                print(
                    "Product card found at level:",
                    level
                )

                return candidate

        except Exception:

            continue

    return None

# ============================================================
# GET PRODUCTS
# ============================================================

def get_products(page, product):

    results = []

    product_found = False

    print(
        "Waiting for NEONET products..."
    )

    # ========================================================
    # STORAGE NORMALIZATION
    #
    # Treat:
    #
    # 1T
    # 1TB
    # 1000GB
    #
    # as the same storage configuration.
    # ========================================================

    def normalize_storage(value):

        if value is None:
            return None

        text = (
            str(value)
            .upper()
            .replace("\u00A0", " ")
            .strip()
        )

        text = re.sub(
            r"\s+",
            "",
            text
        )

        # ----------------------------------------------------
        # 1T / 1TB
        # ----------------------------------------------------

        tb_match = re.fullmatch(
            r"(\d+(?:\.\d+)?)TB?",
            text
        )

        if tb_match:

            try:

                return str(
                    int(
                        float(
                            tb_match.group(1)
                        ) * 1000
                    )
                )

            except ValueError:

                return None

        # ----------------------------------------------------
        # 512GB / 256GB / 1000GB
        # ----------------------------------------------------

        gb_match = re.search(
            r"(\d+)\s*GB",
            text
        )

        if gb_match:

            return gb_match.group(1)

        # ----------------------------------------------------
        # Plain number
        #
        # Example:
        # 512
        # ----------------------------------------------------

        number_match = re.fullmatch(
            r"\d+",
            text
        )

        if number_match:

            return number_match.group()

        return None


    # ========================================================
    # CONFIGURATION EXTRACTION
    #
    # Supports:
    #
    # 12/512GB
    # 12 / 512 GB
    # 12/1TB
    # 12/1T
    # 8/256GB
    # ========================================================

    def get_configuration(text):

        if not text:

            return None, None

        text = str(text)

        match = re.search(
            r"(\d+)\s*/\s*"
            r"(\d+(?:\.\d+)?)\s*"
            r"(GB|TB|T)\b",
            text,
            re.IGNORECASE
        )

        if match:

            ram_value = match.group(1)

            storage_value = (
                match.group(2)
                + match.group(3)
            )

            storage_normalized = normalize_storage(
                storage_value
            )

            if storage_normalized:

                return (
                    ram_value + " GB",
                    storage_normalized + " GB"
                )

        return None, None


    # ========================================================
    # TARGET RAM / STORAGE
    # ========================================================

    target_ram = re.sub(
        r"\D",
        "",
        str(product["ram"])
    )

    target_storage = normalize_storage(
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

    # ========================================================
    # WAIT FOR PRODUCTS
    # ========================================================

    try:

        page.wait_for_selector(
            "h3",
            timeout=15000
        )

    except Exception:

        print(
            "Could not find NEONET product headings."
        )

        return [

            {
                "product_name":
                    product["name"],

                "variant":
                    "Unknown",

                "ram":
                    str(product["ram"]) + " GB",

                "storage":
                    (
                        str(target_storage) + " GB"
                        if target_storage
                        else str(product["storage"])
                    ),

                "price":
                    None,

                "availability":
                    "Unavailable"
            }

        ]

    # ========================================================
    # FIND PRODUCT HEADINGS
    # ========================================================

    headings = page.locator(
        "h3"
    )

    count = headings.count()

    print(
        "Total NEONET H3:",
        count
    )

    # ========================================================
    # PROCESS PRODUCTS
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

        if not title:

            continue

        print()
        print("=" * 60)
        print(
            "NEONET PRODUCT",
            i
        )
        print("=" * 60)

        print(
            "TITLE:",
            title
        )

        # ====================================================
        # PRODUCT NAME MATCHING
        #
        # Uses your existing strict matches_product() function.
        #
        # No 5G exception is added here yet.
        # ====================================================

        if not matches_product(
            title,
            product
        ):

            continue

        # ====================================================
        # RAM / STORAGE FROM TITLE
        # ====================================================

        ram, storage = get_configuration(
            title
        )

        print(
            "TITLE RAM:",
            ram
        )

        print(
            "TITLE STORAGE:",
            storage
        )

        # ====================================================
        # FIND PRODUCT CARD
        #
        # We find the card before giving up, because sometimes
        # the title may not contain the configuration.
        # ====================================================

        card = find_product_card(
            heading
        )

        if card is None:

            print(
                "Could not find a tight product card."
            )

            continue

        try:

            card_text = (
                card
                .inner_text()
                .strip()
            )

        except Exception:

            print(
                "Could not read product card."
            )

            continue

        print()
        print(
            "CARD TEXT:"
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

        # ====================================================
        # FALLBACK: GET CONFIGURATION FROM CARD
        # ====================================================

        if ram is None or storage is None:

            card_ram, card_storage = get_configuration(
                card_text
            )

            if card_ram is not None:

                ram = card_ram

            if card_storage is not None:

                storage = card_storage

        # ====================================================
        # FALLBACK: RAM / STORAGE FROM SPECIFICATIONS
        # ====================================================

        if ram is None:

            ram_match = re.search(
                r"Pamięć\s+RAM:\s*"
                r"(\d+)\s*GB",
                card_text,
                re.IGNORECASE
            )

            if ram_match:

                ram = (
                    ram_match.group(1)
                    + " GB"
                )

        if storage is None:

            storage_match = re.search(
                r"Pamięć\s+wbudowana:\s*"
                r"(\d+(?:\.\d+)?)\s*"
                r"(GB|TB|T)\b",
                card_text,
                re.IGNORECASE
            )

            if storage_match:

                storage_value = (
                    storage_match.group(1)
                    + storage_match.group(2)
                )

                normalized_storage = normalize_storage(
                    storage_value
                )

                if normalized_storage:

                    storage = (
                        normalized_storage
                        + " GB"
                    )

        print(
            "FINAL RAM:",
            ram
        )

        print(
            "FINAL STORAGE:",
            storage
        )

        # ====================================================
        # MATCH TARGET RAM / STORAGE
        # ====================================================

        ram_number = re.sub(
            r"\D",
            "",
            str(ram)
        )

        storage_number = normalize_storage(
            storage
        )

        if (
            ram_number != target_ram
            or
            storage_number != target_storage
        ):

            print(
                "RAM / Storage mismatch."
            )

            print(
                "Expected:",
                target_ram,
                "GB /",
                target_storage,
                "GB"
            )

            print(
                "Found:",
                ram_number,
                "GB /",
                storage_number,
                "GB"
            )

            continue

        print(
            "RAM / Storage MATCH."
        )

        # ====================================================
        # CORRECT PRODUCT FOUND
        # ====================================================

        product_found = True

        # ====================================================
        # COLOR
        # ====================================================

        color = get_color(
            title
        )

        print(
            "COLOR:",
            color
        )

        # ====================================================
        # AVAILABILITY
        # ====================================================

        availability = matching.classify_availability(card_text)

        print(
            "AVAILABILITY:",
            availability
        )

        # ====================================================
        # PRICE
        # ====================================================

        price = clean_price(
            card_text
        )

        print(
            "PRICE:",
            price
        )

        # ====================================================
        # RESULT
        # ====================================================

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

    if not product_found:

        print()
        print("=" * 60)

        print(
            "NEONET: Target product/configuration not found."
        )

        print(
            "Product:",
            product["name"]
        )

        print(
            "RAM:",
            product["ram"]
        )

        print(
            "Storage:",
            product["storage"]
        )

        print("=" * 60)

        results.append({

            "product_name":
                product["name"],

            "variant":
                "Unknown",

            "ram":
                str(product["ram"]) + " GB",

            "storage":
                (
                    str(target_storage) + " GB"
                    if target_storage
                    else str(product["storage"])
                ),

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
        "NEONET RESULTS:",
        len(results)
    )

    print("=" * 60)

    for result in results:

        print(
            result
        )

    return results

# ============================================================
# COMPATIBILITY FUNCTIONS
# ============================================================

def get_price_results(page, product):

    return get_products(
        page,
        product
    )


def get_price(page, product):

    return get_products(
        page,
        product
    )