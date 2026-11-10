import re

try:
    from . import matching      # imported as scrapers.<site> (normal case)
except ImportError:             # run as a plain script
    import matching
import unicodedata


# ============================================================
# PRICE
# ============================================================

def clean_price(price_text):

    if price_text is None:
        return None

    text = str(price_text).strip()

    text = text.replace("Cena:", "")
    text = text.replace("zł", "")
    text = text.replace("PLN", "")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u202f", " ")

    text = re.sub(
        r"[^0-9,.\s]",
        "",
        text
    )

    text = text.strip()

    if not text:
        return None

    # Remove spaces used as thousand separators
    text = re.sub(
        r"\s+",
        "",
        text
    )

    # Polish format: 3 999,00
    if "," in text and "." in text:

        text = text.replace(".", "")
        text = text.replace(",", ".")

    elif "," in text:

        text = text.replace(",", ".")

    try:
        return float(text)

    except ValueError:
        return None


# ============================================================
# STORAGE NORMALIZATION
# ============================================================

def normalize_storage(value):

    """
    Convert different storage formats to GB.

    Examples:
        256      -> 256
        256GB    -> 256
        1T       -> 1000
        1TB      -> 1000
        1000 GB  -> 1000
    """

    if value is None:
        return None

    text = str(value).upper()

    text = text.replace(" ", "")
    text = text.replace("\u00A0", "")

    # 1T / 1TB
    match = re.search(
        r"(\d+(?:[.,]\d+)?)T(?:B)?\b",
        text
    )

    if match:

        try:
            return str(
                int(
                    float(
                        match.group(1).replace(",", ".")
                    ) * 1000
                )
            )

        except ValueError:
            return None

    # GB
    match = re.search(
        r"(\d+)\s*GB",
        text
    )

    if match:
        return match.group(1)

    # Plain number
    match = re.search(
        r"\d+",
        text
    )

    if match:
        return match.group(0)

    return None


def format_storage(value):

    """
    Format storage nicely for output.
    """

    normalized = normalize_storage(value)

    if normalized is None:
        return str(value)

    if normalized == "1000":
        return "1 TB"

    return normalized + " GB"


# ============================================================
# COLOR
# ============================================================

def _get_color_base(title):

    title_lower = (
        str(title)
        .lower()
    )

    color_map = {

        # BLACK
        "midnight black": "Black",
        "czarny": "Black",
        "czarna": "Black",
        "black": "Black",

        # BLUE
        "glacier blue": "Blue",
        "ocean blue": "Blue",
        "niebieski": "Blue",
        "niebieska": "Blue",
        "blue": "Blue",

        # GREEN
        "forest green": "Green",
        "zielony": "Green",
        "zielona": "Green",
        "green": "Green",

        # PURPLE
        "aurora purple": "Purple",
        "fioletowy": "Purple",
        "fioletowa": "Purple",
        "purple": "Purple",

        # TITANIUM
        "tytanowy": "Titanium",
        "tytanowa": "Titanium",
        "titanium": "Titanium",

        # WHITE
        "biały": "White",
        "biała": "White",
        "white": "White",

        # GREY
        "szary": "Grey",
        "szara": "Grey",
        "grey": "Grey",
        "gray": "Grey",

        # SILVER
        "srebrny": "Silver",
        "srebrna": "Silver",
        "silver": "Silver",

        # GOLD
        "złoty": "Gold",
        "złota": "Gold",
        "gold": "Gold",

        # ORANGE
        "pomarańczowy": "Orange",
        "orange": "Orange",

        # PINK
        "różowy": "Pink",
        "różowa": "Pink",
        "pink": "Pink",

        # BROWN
        "brązowy": "Brown",
        "brązowa": "Brown",
        "brown": "Brown",
    }

    # Longer names first
    for color_name in sorted(
        color_map.keys(),
        key=len,
        reverse=True
    ):

        if color_name in title_lower:
            return color_map[color_name]

    return "Unknown"



def get_color(title):

    """Scraper colour list first, shared wide list as fallback."""

    colour = _get_color_base(title)

    if colour == "Unknown":
        colour = matching.detect_colour(title)

    return colour


# ============================================================
# PRODUCT NAME NORMALIZATION
# ============================================================

def normalize_product_text(text):

    text = str(text).lower()

    # Remove accents
    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        c
        for c in text
        if not unicodedata.combining(c)
    )

    text = text.replace(
        "\u00a0",
        " "
    )

    # Normalize Pro+
    text = re.sub(
        r"\bpro\s*\+",
        "pro+",
        text
    )

    # Separate punctuation
    text = re.sub(
        r"[/(),;:_\-]+",
        " ",
        text
    )

    # Keep letters, numbers, spaces and +
    text = re.sub(
        r"[^a-z0-9+\s]",
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


# ============================================================
# PRODUCT MATCHING
# ============================================================

# ============================================================
# PRODUCT MATCHING
# ============================================================

def normalize_product_name(text):

    text = str(text).lower().strip()

    # Normalize Pro+
    text = re.sub(
        r"pro\s*\+",
        "pro+",
        text
    )

    # Remove punctuation
    text = re.sub(
        r"[^a-z0-9+]+",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def is_17t_family(text):

    normalized = normalize_product_name(text)

    return bool(
        re.search(
            r"\bxiaomi 17t\b",
            normalized
        )
    )


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
    # SPECIAL CASE:
    # XIAOMI 17T FAMILY
    #
    # KTR often omits "5G" from product titles.
    # Only for the 17T family, ignore 5G.
    # ========================================================

    if (
        is_17t_family(target_normalized)
        and
        is_17t_family(title_normalized)
    ):

        target_normalized = re.sub(
            r"\b5g\b",
            "",
            target_normalized
        )

        title_normalized = re.sub(
            r"\b5g\b",
            "",
            title_normalized
        )

        target_normalized = re.sub(
            r"\s+",
            " ",
            target_normalized
        ).strip()

        title_normalized = re.sub(
            r"\s+",
            " ",
            title_normalized
        ).strip()

    # ========================================================
    # STRICT PRODUCT MATCHING
    #
    # The target name must appear as a complete phrase.
    # ========================================================

    pattern = (
        r"(?:^|\s)"
        +
        re.escape(target_normalized)
        +
        r"(?=$|\s)"
    )

    match = re.search(
        pattern,
        title_normalized
    )

    if not match:

        return False

    # ========================================================
    # CHECK WHAT COMES AFTER THE MATCH
    #
    # Prevent:
    #
    # Redmi Note 15 Pro
    # matching
    # Redmi Note 15 Pro 5G
    #
    # Redmi Note 15
    # matching
    # Redmi Note 15 Pro
    #
    # ========================================================

    remaining = (
        title_normalized[match.end():]
        .strip()
    )

    if remaining:

        next_word = remaining.split()[0]

        model_modifiers = {
            "5g",
            "pro",
            "pro+",
            "ultra",
            "lite",
            "max",
            "plus",
            "+",
        }

        if next_word in model_modifiers:

            return False

    return True

# ============================================================
# PRICE EXTRACTION
# ============================================================

def extract_price(card):

    price_element = card.locator(
        '[data-price-type="final"]'
    ).first

    if price_element.count() > 0:

        price_text = (
            price_element
            .inner_text()
            .strip()
        )

        price = clean_price(
            price_text
        )

        if price is not None:
            return price

    return None


# ============================================================
# RAM / STORAGE EXTRACTION
# ============================================================

def extract_ram_storage(card_text, title):

    ram = None
    storage = None

    # Combine title and card text
    full_text = f"{title}\n{card_text}"

    # ========================================================
    # RAM - SPECIFICATIONS
    # ========================================================

    ram_patterns = [

        r"Pamięć\s+RAM\s*:\s*(\d+)\s*GB",

        r"\bRAM\s*:\s*(\d+)\s*GB",

    ]

    for pattern in ram_patterns:

        match = re.search(
            pattern,
            card_text,
            re.IGNORECASE
        )

        if match:

            ram = match.group(1) + " GB"
            break

    # ========================================================
    # STORAGE - SPECIFICATIONS
    # ========================================================

    storage_patterns = [

        r"Pamięć\s+Flash\s*:\s*"
        r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)",

        r"Pamięć\s+wbudowana\s*:\s*"
        r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)",

        r"Pamięć\s+wewnętrzna\s*:\s*"
        r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)",

        r"Pojemność\s+pamięci\s*:\s*"
        r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)",

        r"\bDysk\s*:\s*"
        r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)",

    ]

    for pattern in storage_patterns:

        match = re.search(
            pattern,
            card_text,
            re.IGNORECASE
        )

        if match:

            raw_storage = (
                match.group(1)
                + match.group(2)
            )

            storage = format_storage(raw_storage)

            break

    # ========================================================
    # CONFIGURATION FALLBACK
    # ========================================================

    if ram is None or storage is None:

        config_patterns = [

            # 12 GB / 512 GB
            r"\b(\d+)\s*GB\s*/\s*"
            r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)\b",

            # 12GB/512GB
            r"\b(\d+)\s*GB\s*/\s*"
            r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)\b",

            # 12 / 512 GB
            r"\b(\d+)\s*/\s*"
            r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)\b",

            # 12+512 GB
            r"\b(\d+)\s*\+\s*"
            r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)\b",

            # 12 GB + 512 GB
            r"\b(\d+)\s*GB\s*\+\s*"
            r"(\d+(?:[.,]\d+)?)\s*(TB|T|GB)\b",

            # 12/512  (no GB shown)
            r"\b(4|6|8|12|16|24)\s*/\s*"
            r"(64|128|256|512|1000|1024)\b",

            # 12+512 (no GB shown)
            r"\b(4|6|8|12|16|24)\s*\+\s*"
            r"(64|128|256|512|1000|1024)\b",

        ]

        for pattern in config_patterns:

            match = re.search(
                pattern,
                full_text,
                re.IGNORECASE
            )

            if not match:
                continue

            config_ram = match.group(1)

            if len(match.groups()) >= 3:

                config_storage_value = match.group(2)
                config_storage_unit = match.group(3)

                raw_storage = (
                    config_storage_value
                    + config_storage_unit
                )

            else:

                # Unitless fallback like 12/512
                raw_storage = match.group(2) + "GB"

            if ram is None:
                ram = config_ram + " GB"

            if storage is None:
                storage = format_storage(raw_storage)

            break

    return ram, storage


# ============================================================
# PRODUCTS
# ============================================================

def get_products(page, product):

    results = []

    print()
    print("=" * 60)
    print("Waiting for KTR products...")
    print("=" * 60)

    cards = page.locator(
        'div[data-name="listingTile"]'
    )

    try:

        cards.first.wait_for(
            state="visible",
            timeout=30000
        )

    except Exception:

        print(
            "KTR product cards did not become visible."
        )

    print(
        "KTR product cards:",
        cards.count()
    )

    # --------------------------------------------------------
    # TARGET CONFIGURATION
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
        "TARGET PRODUCT:",
        product["name"]
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
    # Track matching product
    # --------------------------------------------------------

    product_found = False

    # --------------------------------------------------------
    # PROCESS CARDS
    # --------------------------------------------------------

    for i in range(cards.count()):

        card = cards.nth(i)

        print()
        print("=" * 60)
        print(
            "KTR CARD",
            i
        )
        print("=" * 60)

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title_element = card.locator(
            "h2"
        ).first

        if title_element.count() == 0:

            print(
                "No H2 title found."
            )

            continue

        title = (
            title_element
            .inner_text()
            .strip()
        )

        print(
            "TITLE:",
            title
        )

        # ----------------------------------------------------
        # PRODUCT MATCHING
        # ----------------------------------------------------

        if not product_name_matches(
            product["name"],
            title
        ):
            print("Product name mismatch.")
            continue

        print(
            "PRODUCT NAME MATCH: YES"
        )

        # ----------------------------------------------------
        # CARD TEXT
        # ----------------------------------------------------

        card_text = (
            card
            .inner_text()
            .strip()
        )

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

        # ----------------------------------------------------
        # EXCLUDE OUTLET
        # ----------------------------------------------------

        if "outlet" in card_text.lower():

            print(
                "SKIPPING OUTLET PRODUCT"
            )

            continue

        # ----------------------------------------------------
        # RAM / STORAGE
        # ----------------------------------------------------

        ram, storage = extract_ram_storage(
            card_text,
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

        actual_ram = re.sub(
            r"\D",
            "",
            str(ram)
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

        # ----------------------------------------------------
        # MATCH CONFIGURATION
        # ----------------------------------------------------

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

        # Matching configuration found
        product_found = True

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

        availability = matching.classify_availability(card_text)

        print(
            "AVAILABILITY:",
            availability
        )

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price = extract_price(
            card
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
    # NOT FOUND
    # ========================================================

    if not product_found:

        print()
        print("=" * 60)
        print(
            "KTR: TARGET PRODUCT NOT FOUND"
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
                format_storage(
                    product["storage"]
                ),

            "price":
                None,

            "availability":
                "Unavailable",
        })

    return results


# ============================================================
# UNIFIED INTERFACE
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