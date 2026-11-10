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

    text = str(text).strip()

    # Remove common currency text
    text = (
        text
        .replace("\u00a0", " ")
        .replace("zł", "")
        .replace("PLN", "")
        .strip()
    )

    # Find a normal price, for example:
    # 899,00
    # 899.00
    # 1 899,00

    match = re.search(
        r"(\d[\d\s]*[,.]\d{1,2})",
        text
    )

    if match:

        value = (
            match.group(1)
            .replace(" ", "")
            .replace(",", ".")
        )

        try:
            return float(value)

        except ValueError:
            pass

    # Integer price fallback
    match = re.search(
        r"\b(\d{2,5})\b",
        text
    )

    if match:

        try:
            return float(
                match.group(1)
            )

        except ValueError:
            pass

    return None


# ============================================================
# PRODUCT NORMALIZATION / MATCHING
# ============================================================

def normalize_product_text(text):

    text = (
        str(text)
        .lower()
        .replace("\u00a0", " ")
        .strip()
    )

    # Normalize Pro+ versions
    text = re.sub(
        r"\bpro\s*\+",
        "pro+",
        text
    )

    # Replace punctuation with spaces
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
    # SPECIAL CASES:
    #
    # Some product families may omit 5G in our target name,
    # while the website includes 5G in the title.
    #
    # For these families only, ignore the 5G difference:
    #
    # - Xiaomi 17 family
    # - POCO X8 family
    # --------------------------------------------------------

    is_xiaomi_17_family = bool(
        re.search(
            r"\bxiaomi 17(?:\s|$)",
            target_normalized
        )
    )

    is_poco_x8_family = bool(
        re.search(
            r"\bpoco x8(?:\s|$)",
            target_normalized
        )
    )

    ignore_5g_difference = (
        is_xiaomi_17_family
        or
        is_poco_x8_family
    )

    # --------------------------------------------------------
    # STYLUS / PEN / RYSIK BUNDLE MATCHING
    #
    # Products sold with a Stylus/Rysik must not be mixed with
    # the normal product unless the target explicitly contains
    # a Stylus/Rysik indicator.
    #
    # Media Expert may use the Polish word "Rysik".
    # --------------------------------------------------------

    stylus_pattern = (
        r"\b(?:stylus|rysik)\b"
    )

    target_has_stylus = bool(
        re.search(
            stylus_pattern,
            target_normalized
        )
    )

    title_has_stylus = bool(
        re.search(
            stylus_pattern,
            title_normalized
        )
    )

    print(
        "TARGET HAS STYLUS/RYSIK:",
        target_has_stylus
    )

    print(
        "TITLE HAS STYLUS/RYSIK:",
        title_has_stylus
    )

    if target_has_stylus != title_has_stylus:

        print(
            "Product mismatch: Stylus/Rysik bundle "
            "does not match."
        )

        return False

    # --------------------------------------------------------
    # 4G / LTE MATCHING
    #
    # IMPORTANT:
    #
    # Do NOT apply this rule globally.
    #
    # Only protect the base Redmi Pad 2 from being mixed
    # with Redmi Pad 2 4G / LTE versions.
    #
    # For normal smartphones, Media Expert may include
    # "4G LTE" in the title even when the target name
    # does not include it.
    # --------------------------------------------------------

    is_base_redmi_pad_2 = bool(
        re.fullmatch(
            r"redmi pad 2",
            target_normalized
        )
    )

    if is_base_redmi_pad_2:

        title_has_lte_or_4g = bool(
            re.search(
                r"\b(?:4g|lte)\b",
                title_normalized
            )
        )

        target_has_lte_or_4g = bool(
            re.search(
                r"\b(?:4g|lte)\b",
                target_normalized
            )
        )

        if target_has_lte_or_4g != title_has_lte_or_4g:

            print(
                "Product mismatch: Redmi Pad 2 connectivity "
                "version does not match."
            )

            return False

    # --------------------------------------------------------
    # 5G MATCHING
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

    # --------------------------------------------------------
    # Strict 5G matching for everything except the
    # explicitly defined special families
    # --------------------------------------------------------

    if not ignore_5g_difference:

        if target_has_5g != title_has_5g:

            print(
                "Product mismatch: 5G version does not match."
            )

            return False

    else:

        print(
            "Special product family: "
            "ignoring 5G naming difference."
        )

    # --------------------------------------------------------
    # Remove connectivity labels for core product comparison
    #
    # 4G/LTE has only been treated specially for Redmi Pad 2.
    # 5G has already been checked according to the rules above.
    # --------------------------------------------------------

    target_core = re.sub(
        r"\b(?:5g|lte|4g)\b",
        "",
        target_normalized
    )

    title_core = re.sub(
        r"\b(?:5g|lte|4g)\b",
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
    # Product modifiers
    #
    # These must remain distinct.
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
        # Prevent shorter models matching longer versions
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
            "PRODUCT NAME MATCH: YES"
        )

        return True

    print(
        "Product name mismatch."
    )

    return False

    # --------------------------------------------------------
    # 5G MATCHING
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

    # --------------------------------------------------------
    # Strict 5G matching for everything except the
    # explicitly defined special families
    # --------------------------------------------------------

    if not ignore_5g_difference:

        if target_has_5g != title_has_5g:

            print(
                "Product mismatch: 5G version does not match."
            )

            return False

    else:

        print(
            "Special product family: ignoring 5G naming difference."
        )

    # --------------------------------------------------------
    # Remove connectivity labels for core product comparison
    #
    # LTE/4G has already been checked strictly above.
    # 5G has already been checked according to the rules above.
    # --------------------------------------------------------

    target_core = re.sub(
        r"\b(?:5g|lte|4g)\b",
        "",
        target_normalized
    )

    title_core = re.sub(
        r"\b(?:5g|lte|4g)\b",
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
    # Product modifiers
    #
    # These must remain distinct.
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
        # Prevent shorter models matching longer versions
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
            "PRODUCT NAME MATCH: YES"
        )

        return True

    print(
        "Product name mismatch."
    )

    return False


# ============================================================
# COLOR
# ============================================================

def _get_color_base(text):

    if not text:
        return "Unknown"

    text_lower = (
        str(text)
        .lower()
        .replace("\u00a0", " ")
    )

    # --------------------------------------------------------
    # Marketing colors
    # --------------------------------------------------------

    if "glacier blue" in text_lower:
        return "Blue"

    elif "ocean blue" in text_lower:
        return "Blue"

    elif "sky blue" in text_lower:
        return "Blue"

    elif "ocean teal" in text_lower:
        return "Green"

    elif "midnight black" in text_lower:
        return "Black"

    elif "forest green" in text_lower:
        return "Green"

    elif "aurora purple" in text_lower:
        return "Purple"

    elif "mocha brown" in text_lower:
        return "Brown"

    # --------------------------------------------------------
    # English colors
    # --------------------------------------------------------

    elif re.search(r"\bblack\b", text_lower):
        return "Black"

    elif re.search(r"\bgreen\b", text_lower):
        return "Green"

    elif re.search(r"\bblue\b", text_lower):
        return "Blue"

    elif re.search(r"\bwhite\b", text_lower):
        return "White"

    elif re.search(r"\bgrey\b", text_lower):
        return "Grey"

    elif re.search(r"\bgray\b", text_lower):
        return "Grey"

    elif re.search(r"\bsilver\b", text_lower):
        return "Silver"

    elif re.search(r"\bgold\b", text_lower):
        return "Gold"

    elif re.search(r"\bpurple\b", text_lower):
        return "Purple"

    elif re.search(r"\bpink\b", text_lower):
        return "Pink"

    elif re.search(r"\bbrown\b", text_lower):
        return "Brown"

    elif re.search(r"\btitanium\b", text_lower):
        return "Titanium"

    # --------------------------------------------------------
    # Polish colors
    # --------------------------------------------------------

    elif "czarn" in text_lower:
        return "Black"

    elif "zielon" in text_lower:
        return "Green"

    elif "niebiesk" in text_lower:
        return "Blue"

    elif "biały" in text_lower or "bialy" in text_lower:
        return "White"

    elif "szar" in text_lower:
        return "Grey"

    elif "srebr" in text_lower:
        return "Silver"

    elif "złot" in text_lower or "zlot" in text_lower:
        return "Gold"

    elif "fiolet" in text_lower:
        return "Purple"

    elif "Pomarańczowy" in text_lower:
        return "Orange"

    elif "róż" in text_lower or "roz" in text_lower:
        return "Pink"

    elif "brąz" in text_lower or "braz" in text_lower:
        return "Brown"

    elif "tytan" in text_lower:
        return "Titanium"

    return "Unknown"


def get_color(text):

    """Scraper colour list first, shared wide list as fallback."""

    colour = _get_color_base(text)

    if colour == "Unknown":
        colour = matching.detect_colour(text)

    return colour


def normalize_storage(value):

    if value is None:
        return None

    text = str(value).upper().strip()

    # Remove spaces
    text = re.sub(r"\s+", "", text)

    # 1T / 1TB -> 1000 GB
    tb_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)TB?",
        text
    )

    if tb_match:

        tb_value = float(
            tb_match.group(1)
        )

        return str(
            int(tb_value * 1000)
        )

    # Normal GB values
    gb_match = re.search(
        r"\d+",
        text
    )

    if gb_match:

        return gb_match.group()

    return None

# ============================================================
# RAM / STORAGE
# ============================================================

def get_ram_storage(card_text, title):

    ram = None
    storage = None

    # --------------------------------------------------------
    # Media Expert card format
    #
    # Pamięć RAM/Wewnętrzna:
    # 8 GB / 256 GB
    # --------------------------------------------------------

    memory_match = re.search(
        r"Pamięć\s*RAM\s*/\s*Wewnętrzna:\s*"
        r"(\d+)\s*GB\s*/\s*(\d+)\s*GB",
        card_text,
        re.IGNORECASE
    )

    if memory_match:

        return (
            memory_match.group(1),
            memory_match.group(2)
        )

    # --------------------------------------------------------
    # Alternative format:
    #
    # 8 GB / 256 GB
    # --------------------------------------------------------

    memory_match = re.search(
        r"(\d+)\s*GB\s*/\s*(\d+)\s*GB",
        card_text,
        re.IGNORECASE
    )

    if memory_match:

        return (
            memory_match.group(1),
            memory_match.group(2)
        )

    # --------------------------------------------------------
    # Title fallback:
    #
    # Redmi Note 15 Pro 8/256GB
    # --------------------------------------------------------

    title_match = re.search(
        r"(\d+)\s*/\s*(\d+)\s*GB",
        title,
        re.IGNORECASE
    )

    if title_match:

        return (
            title_match.group(1),
            title_match.group(2)
        )

    return ram, storage


# ============================================================
# PRICE EXTRACTION
# ============================================================

def extract_price(card):

    card_text = (
        card
        .inner_text()
        .strip()
    )

    card_text_lower = card_text.lower()

    # --------------------------------------------------------
    # Unavailable products normally do not have a valid price
    # --------------------------------------------------------

    if (
        "produkt chwilowo niedostępny"
        in card_text_lower
        or
        "produkt niedostępny"
        in card_text_lower
    ):

        return None

    # --------------------------------------------------------
    # Media Expert price structure:
    #
    # span.whole   -> 899
    # span.decimal -> 00
    # --------------------------------------------------------

    whole_elements = card.locator(
        "span.whole"
    )

    decimal_elements = card.locator(
        "span.decimal"
    )

    if whole_elements.count() > 0:

        for i in range(
            whole_elements.count()
        ):

            try:

                whole = (
                    whole_elements
                    .nth(i)
                    .inner_text()
                    .strip()
                )

                # Avoid unrelated small numbers
                whole_clean = re.sub(
                    r"\D",
                    "",
                    whole
                )

                if not whole_clean:

                    continue

                if int(whole_clean) < 50:

                    continue

                decimal = "00"

                if (
                    decimal_elements.count()
                    > i
                ):

                    decimal_text = (
                        decimal_elements
                        .nth(i)
                        .inner_text()
                        .strip()
                    )

                    decimal_match = re.search(
                        r"\d{1,2}",
                        decimal_text
                    )

                    if decimal_match:

                        decimal = (
                            decimal_match
                            .group()
                            .zfill(2)
                        )

                try:

                    return float(
                        f"{whole_clean}.{decimal}"
                    )

                except ValueError:

                    continue

            except Exception:

                continue

    # --------------------------------------------------------
    # Fallback:
    #
    # Look for normal prices in card text
    # --------------------------------------------------------

    matches = re.findall(
        r"(\d[\d\s]*[,.]\d{2})\s*zł",
        card_text,
        re.IGNORECASE
    )

    if matches:

        for match in matches:

            value = (
                match
                .replace(" ", "")
                .replace(",", ".")
            )

            try:

                price = float(value)

                if price >= 50:

                    return price

            except ValueError:

                continue

    return None


# ============================================================
# OLD SIMPLE PRICE FUNCTION
# ============================================================

def get_price_only(page):

    price_elements = page.locator(
        "span.whole"
    )

    if price_elements.count() == 0:

        raise ValueError(
            "Media Expert price element not found."
        )

    whole = (
        price_elements
        .first
        .inner_text()
        .strip()
    )

    decimal_elements = page.locator(
        "span.decimal"
    )

    decimal = "00"

    if decimal_elements.count() > 0:

        decimal_text = (
            decimal_elements
            .first
            .inner_text()
            .strip()
        )

        decimal_match = re.search(
            r"\d{1,2}",
            decimal_text
        )

        if decimal_match:

            decimal = (
                decimal_match
                .group()
                .zfill(2)
            )

    whole_clean = re.sub(
        r"\D",
        "",
        whole
    )

    return clean_price(
        f"{whole_clean}.{decimal}"
    )


# ============================================================
# PRODUCTS
# ============================================================

def get_products(page, product):

    print(
        "Loading all Media Expert products..."
    )

    # --------------------------------------------------------
    # Load all products on the page
    # --------------------------------------------------------

    previous_count = 0
    stable_rounds = 0

    for _ in range(15):

        page.mouse.wheel(
            0,
            1500
        )

        page.wait_for_timeout(
            1000
        )

        current_count = page.locator(
            "h2, h3"
        ).count()

        print(
            "Current h2/h3 count:",
            current_count
        )

        if current_count == previous_count:

            stable_rounds += 1

        else:

            stable_rounds = 0

        previous_count = current_count

        if stable_rounds >= 2:

            break

    print(
        "Finished loading products. Total h2/h3:",
        page.locator("h2, h3").count()
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    results = []

    product_found = False

    titles = page.locator(
        "h2, h3"
    )

    print(
        "Total h2/h3 elements:",
        titles.count()
    )

    # --------------------------------------------------------
    # Target RAM / storage
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
        target_storage,
        "GB"
    )

    # --------------------------------------------------------
    # Process products
    # --------------------------------------------------------

    for i in range(titles.count()):

        try:

            title_element = titles.nth(i)

            title = (
                title_element
                .inner_text()
                .strip()
            )

            if not title:

                continue

            # ------------------------------------------------
            # Product matching
            # ------------------------------------------------

            if not matches_product(
                title,
                product
            ):

                continue

            print()
            print("=" * 60)
            print(
                "MEDIA EXPERT PRODUCT",
                i
            )
            print("=" * 60)

            print(
                "TITLE:",
                title
            )

            # ------------------------------------------------
            # Find product card
            # ------------------------------------------------

            card = title_element.locator(
                "xpath=ancestor::div[contains(@class, 'offer-box')]"
            ).first

            if card.count() == 0:

                print(
                    "Offer card not found."
                )

                continue

            card_text = (
                card
                .inner_text()
                .strip()
            )

            # ------------------------------------------------
            # OUTLET PRODUCTS
            #
            # Do not use outlet / clearance products
            # as normal competitor offers.
            # ------------------------------------------------

            if (
                "outlet" in title.lower()
                or
                "outlet" in card_text.lower()
            ):

                print(
                    "Skipping OUTLET product."
                )

                continue

            # ------------------------------------------------
            # RAM / STORAGE
            # ------------------------------------------------

            ram, storage = get_ram_storage(
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

            # ------------------------------------------------
            # Normalize RAM / storage
            # ------------------------------------------------

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
                actual_storage,
                "GB"
            )

            # ------------------------------------------------
            # Match RAM / storage
            # ------------------------------------------------

            if (
                actual_ram != target_ram
                or
                actual_storage != target_storage
            ):

                print(
                    "RAM/storage does not match target."
                )

                continue

            print(
                "RAM / STORAGE MATCH: YES"
            )

            # ------------------------------------------------
            # Exact product found
            # ------------------------------------------------

            product_found = True

            # ------------------------------------------------
            # COLOR
            # ------------------------------------------------

            color = get_color(
                title
            )

            # If not found in title,
            # try the product card text
            if color == "Unknown":

                color_match = re.search(
                    r"Kolor obudowy:\s*([^\n]+)",
                    card_text,
                    re.IGNORECASE
                )

                if color_match:

                    color = get_color(
                        color_match.group(1)
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
            # No stock wording on the card:
            #   a price means it can be bought -> Available
            #   no price and no buy block (Media Expert lists
            #   such offers without a price) -> Unavailable
            # ------------------------------------------------

            if availability == "Unknown":

                availability = (
                    "Available" if price is not None else "Unavailable"
                )

                print(
                    "AVAILABILITY decided from price:",
                    availability
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
                "ERROR PROCESSING PRODUCT:",
                i,
                str(e)
            )

            continue

    # ========================================================
    # TARGET PRODUCT NOT FOUND
    # ========================================================

    if not product_found:

        print()

        print(
            "Target product not found on Media Expert."
        )

        # Format RAM
        target_ram_display = (
            str(product["ram"])
            + " GB"
        )

        # Format storage properly
        original_storage = str(
            product["storage"]
        ).upper()

        if (
            "T" in original_storage
            and
            "GB" not in original_storage
        ):

            target_storage_display = (
                original_storage
                .replace("TB", " TB")
                .replace("T", " TB")
                .strip()
            )

            # Fix possible double spacing / TB
            target_storage_display = re.sub(
                r"\s+",
                " ",
                target_storage_display
            )

        else:

            target_storage_display = (
                str(product["storage"])
                + " GB"
            )

        results.append({

            "product_name":
                product["name"],

            "variant":
                "Unknown",

            "ram":
                target_ram_display,

            "storage":
                target_storage_display,

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
        "MEDIA EXPERT RESULTS:",
        len(results)
    )
    print("=" * 60)

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

        return get_price_only(
            page
        )

    return get_products(
        page,
        product
    )