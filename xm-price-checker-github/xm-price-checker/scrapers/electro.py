import re

try:
    from . import matching
except ImportError:
    import matching


# ============================================================
# PRICE
# ============================================================

def clean_price(text):

    if not text:
        return None

    text = str(text).strip()

    # Remove currency labels
    text = text.replace("zł", "")
    text = text.replace("PLN", "")

    # Remove spaces
    text = text.replace(" ", "")

    # Find price
    match = re.search(
        r"(\d+(?:[,.]\d+)?)",
        text
    )

    if not match:
        return None

    try:
        return float(
            match.group(1).replace(",", ".")
        )

    except ValueError:
        return None


# ============================================================
# STORAGE NORMALIZATION
# ============================================================

def normalize_storage(value):

    """
    Normalize all storage formats to GB.

    Examples:

    256       -> 256
    256 GB    -> 256
    1T        -> 1000
    1TB       -> 1000
    1000 GB   -> 1000
    """

    if value is None:
        return None

    text = (
        str(value)
        .upper()
        .replace(" ", "")
    )

    # --------------------------------------------------------
    # TB / T
    # --------------------------------------------------------

    if re.search(r"1TB|1T\b", text):

        return "1000"

    # --------------------------------------------------------
    # Normal GB values
    # --------------------------------------------------------

    digits = re.sub(
        r"\D",
        "",
        text
    )

    if digits:

        return digits

    return None


# ============================================================
# COLOR
# ============================================================

def _get_color_base(title):

    title_lower = title.lower()

    color_map = {

        # ----------------------------------------------------
        # BLACK
        # ----------------------------------------------------

        "midnight black": "Black",
        "czarny": "Black",
        "czarna": "Black",
        "czarne": "Black",
        "black": "Black",

        # ----------------------------------------------------
        # BLUE
        # ----------------------------------------------------

        "glacier blue": "Blue",
        "ocean blue": "Blue",
        "niebieski": "Blue",
        "niebieska": "Blue",
        "blue": "Blue",

        # ----------------------------------------------------
        # TITANIUM
        # ----------------------------------------------------

        "tytanowy": "Titanium",
        "tytanowa": "Titanium",
        "titanium": "Titanium",

        # ----------------------------------------------------
        # PURPLE
        # ----------------------------------------------------

        "aurora purple": "Purple",
        "lawendowy": "Purple",
        "lawendowa": "Purple",
        "fioletowy": "Purple",
        "fioletowa": "Purple",
        "lavender": "Purple",
        "purple": "Purple",

        # ----------------------------------------------------
        # GREEN
        # ----------------------------------------------------

        "forest green": "Green",
        "zielony": "Green",
        "zielona": "Green",
        "green": "Green",

        # ----------------------------------------------------
        # WHITE
        # ----------------------------------------------------

        "biały": "White",
        "biała": "White",
        "white": "White",

        # ----------------------------------------------------
        # GREY
        # ----------------------------------------------------

        "szary": "Grey",
        "szara": "Grey",
        "grey": "Grey",
        "gray": "Grey",

        # ----------------------------------------------------
        # SILVER
        # ----------------------------------------------------

        "srebrny": "Silver",
        "srebrna": "Silver",
        "silver": "Silver",

        # ----------------------------------------------------
        # orange
        # ----------------------------------------------------

        "Pomarańczowy": "Orange",
        "orange": "Orange",

        # ----------------------------------------------------
        # PINK
        # ----------------------------------------------------

        "różowy": "Pink",
        "różowa": "Pink",
        "pink": "Pink",

        # ----------------------------------------------------
        # BROWN
        # ----------------------------------------------------

        "mocha brown": "Brown",
        "brązowy": "Brown",
        "brązowa": "Brown",
        "brown": "Brown",
    }

    # Check longer/descriptive names first
    for color_name in sorted(
        color_map.keys(),
        key=len,
        reverse=True
    ):

        if re.search(
            rf"\b{re.escape(color_name)}\b",
            title_lower
        ):

            return color_map[color_name]

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

def normalize_product_name(text):

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
    # Remove unnecessary punctuation
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Remove extra spaces
    # --------------------------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ============================================================
# REDMI NOTE SIGNATURE
# ============================================================

def get_redmi_note_signature(text):

    text = normalize_product_name(text)

    # Find Redmi Note number
    match = re.search(
        r"\bredmi note (\d+)\b",
        text
    )

    if not match:
        return None

    model_number = match.group(1)

    after_note = text[match.end():].strip()

    # --------------------------------------------------------
    # Version
    # --------------------------------------------------------

    if re.match(
        r"^pro\+",
        after_note
    ):

        version = "pro+"

    elif re.match(
        r"^pro\b",
        after_note
    ):

        version = "pro"

    else:

        version = "standard"

    # --------------------------------------------------------
    # 5G
    # --------------------------------------------------------

    has_5g = bool(
        re.search(
            r"\b5g\b",
            text
        )
    )

    return (
        model_number,
        version,
        has_5g
    )


# ============================================================
# STRICT PRODUCT MATCHING
# ============================================================

def product_name_matches(target_name, title):

    target_normalized = normalize_product_name(
        target_name
    )

    title_normalized = normalize_product_name(
        title
    )

    print(
        "NORMALIZED TITLE:",
        title_normalized
    )

    print(
        "NORMALIZED TARGET:",
        target_normalized
    )

    # ========================================================
    # STRICT MATCHING FOR REDMI NOTE PRODUCTS
    # ========================================================

    if (
        "redmi note" in target_normalized
        and
        "redmi note" in title_normalized
    ):

        target_signature = get_redmi_note_signature(
            target_name
        )

        title_signature = get_redmi_note_signature(
            title
        )

        if (
            target_signature is not None
            and
            title_signature is not None
        ):

            if target_signature == title_signature:

                print(
                    "Redmi Note signature MATCH."
                )

                return True

            print(
                "Redmi Note signature mismatch."
            )

            return False

    # ========================================================
    # GENERAL STRICT TOKEN MATCHING
    #
    # Prevents:
    #
    # Xiaomi 17
    # matching
    # Xiaomi 17T
    #
    # Xiaomi 17
    # matching
    # Xiaomi 17 Pro
    #
    # Xiaomi 17T
    # matching
    # Xiaomi 17T Pro
    # ========================================================

    target_tokens = target_normalized.split()
    title_tokens = title_normalized.split()

    if not target_tokens:

        return False

    # Product-version words that indicate
    # a different model
    product_modifiers = {

        "pro",
        "pro+",
        "ultra",
        "max",
        "lite",
        "plus",

    }

    # --------------------------------------------------------
    # Look for exact sequence
    # --------------------------------------------------------

    for start in range(

        len(title_tokens)
        -
        len(target_tokens)
        +
        1

    ):

        end = (
            start
            +
            len(target_tokens)
        )

        # Exact token sequence required
        if (
            title_tokens[start:end]
            !=
            target_tokens
        ):

            continue

        # ----------------------------------------------------
        # Check next word
        #
        # Example:
        #
        # Target:
        # Xiaomi 17T
        #
        # Title:
        # Xiaomi 17T Pro
        #
        # -> NOT MATCH
        # ----------------------------------------------------

        if end < len(title_tokens):

            next_token = title_tokens[end]

            if next_token in product_modifiers:

                print(
                    "Product mismatch: "
                    f"additional model version "
                    f"'{next_token}'."
                )

                continue

        # ----------------------------------------------------
        # Exact product model found
        # ----------------------------------------------------

        print(
            "Product name MATCH."
        )

        return True

    print(
        "Product name mismatch."
    )

    return False


# ============================================================
# PRODUCTS
# ============================================================

def get_products(page, product):

    results = []

    print(
        "Waiting for Electro products..."
    )

    # --------------------------------------------------------
    # Find product titles
    # --------------------------------------------------------

    titles = page.locator(
        "h2.name"
    )

    print(
        "Total product titles:",
        titles.count()
    )

    # --------------------------------------------------------
    # Target RAM / Storage
    # --------------------------------------------------------

    target_ram = re.sub(
        r"\D",
        "",
        str(product["ram"])
    )

    target_storage = normalize_storage(
        product["storage"]
    )

    print(
        "TARGET RAM:",
        target_ram
    )

    print(
        "TARGET STORAGE:",
        target_storage
    )

    # --------------------------------------------------------
    # Track whether matching configuration was found
    # --------------------------------------------------------

    product_found = False

    # --------------------------------------------------------
    # Process products
    # --------------------------------------------------------

    for i in range(titles.count()):

        title_element = titles.nth(i)

        title = (
            title_element
            .inner_text()
            .strip()
        )

        # ----------------------------------------------------
        # Match product name
        # ----------------------------------------------------

        if not product_name_matches(
            product["name"],
            title
        ):

            continue

        print()

        print("=" * 60)
        print("ELECTRO PRODUCT", i)
        print("=" * 60)

        print(
            "TITLE:",
            title
        )

        print(
            "PRODUCT NAME MATCH: YES"
        )

        # ----------------------------------------------------
        # Find product container
        # ----------------------------------------------------

        card = title_element.locator(
            "xpath=ancestor::div[contains(@class, 'offer-box')]"
        ).first

        if card.count() == 0:

            print(
                "Could not find product container."
            )

            continue

        # ----------------------------------------------------
        # CARD TEXT
        # ----------------------------------------------------

        card_text = (
            card
            .inner_text()
            .strip()
        )

        # ----------------------------------------------------
        # RAM
        # ----------------------------------------------------

        ram_match = re.search(
            r"Pamięć RAM:\s*([0-9]+\s*GB)",
            card_text,
            re.IGNORECASE
        )

        if ram_match:

            ram = ram_match.group(1)

        else:

            print(
                "RAM not found."
            )

            continue

        # ----------------------------------------------------
        # STORAGE
        # ----------------------------------------------------

        storage_match = re.search(
            r"Pamięć wbudowana\s*\[GB\]:\s*([0-9]+)",
            card_text,
            re.IGNORECASE
        )

        if storage_match:

            storage = (
                storage_match.group(1)
                + " GB"
            )

        else:

            print(
                "Storage not found."
            )

            continue

        # ----------------------------------------------------
        # Match RAM / Storage
        # ----------------------------------------------------

        actual_ram = re.sub(
            r"\D",
            "",
            ram
        )

        actual_storage = normalize_storage(
            storage
        )

        print(
            "ACTUAL RAM:",
            actual_ram
        )

        print(
            "ACTUAL STORAGE:",
            actual_storage
        )

        if actual_ram != target_ram:

            print(
                "Skipping: RAM mismatch."
            )

            continue

        if actual_storage != target_storage:

            print(
                "Skipping: storage mismatch."
            )

            continue

        print(
            "RAM / STORAGE MATCH: YES"
        )

        # ----------------------------------------------------
        # Matching product/configuration found
        # ----------------------------------------------------

        product_found = True

        print(
            "RAM:",
            ram
        )

        print(
            "STORAGE:",
            storage
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

        unavailable_element = card.locator(
            ".product-show-offer-unavailable"
        )

        if unavailable_element.count() > 0:

            availability = "Unavailable"

        else:

            availability = "Available"

        print(
            "AVAILABILITY:",
            availability
        )

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price_element = card.locator(
            "span.whole"
        ).first

        if price_element.count() == 0:

            price = None

        else:

            price_text = (
                price_element
                .inner_text()
                .strip()
            )

            price = clean_price(
                price_text
            )

        print(
            "PRICE:",
            price
        )

        # ----------------------------------------------------
        # SAVE RESULT
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
                availability,

        }

        results.append(
            result
        )

        print(
            "RESULT:",
            result
        )

    # ========================================================
    # PRODUCT NOT FOUND
    # ========================================================

    if not product_found:

        print()

        print("=" * 60)
        print(
            "ELECTRO: TARGET PRODUCT NOT FOUND"
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
            "Storage:",
            product["storage"]
        )

        results.append({

            "product_name":
                product["name"],

            "variant":
                "Unknown",

            "ram":
                str(product["ram"]) + " GB",

            "storage":
                str(product["storage"]),

            "price":
                None,

            "availability":
                "Unavailable",

        })

    return results


# ============================================================
# UNIFIED SCRAPER INTERFACE
# ============================================================

def get_price(page, product=None):

    if product is None:

        # Electro product-page fallback.
        # Kept for compatibility with the unified
        # scraper interface.

        return None

    return get_products(
        page,
        product
    )