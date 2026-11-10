import re

try:
    from . import matching      # imported as scrapers.msh (normal case)
except ImportError:             # run as a plain script
    import matching



# ============================================================
# PRICE
# ============================================================

def clean_price(text):

    if not text:
        return None

    text = str(text).strip()

    text = text.replace("\xa0", " ")

    # Remove spaces
    text = text.replace(" ", "")

    # Keep only digits, comma and dot
    text = re.sub(
        r"[^0-9,.]",
        "",
        text
    )

    if not text:
        return None

    # Polish decimal format
    if "," in text and "." not in text:

        text = text.replace(",", ".")

    # Both thousand separator and decimal separator
    elif "," in text and "." in text:

        # Example: 1.299,99
        if text.rfind(",") > text.rfind("."):

            text = text.replace(".", "")
            text = text.replace(",", ".")

        # Example: 1,299.99
        else:

            text = text.replace(",", "")

    try:

        return float(text)

    except ValueError:

        return None


# ============================================================
# COLOR
# ============================================================

def _get_color_base(title):

    title_lower = (
        str(title)
        .lower()
        .replace("\xa0", " ")
    )

    # --------------------------------------------------------
    # Marketing / combined color names
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
    # Polish colors
    # --------------------------------------------------------

    color_map = {

        "czarn": "Black",

        "zielon": "Green",

        "niebiesk": "Blue",

        "biały": "White",
        "bialy": "White",

        "szar": "Grey",

        "srebr": "Silver",

        "złot": "Gold",
        "zlot": "Gold",

        "pomarańczowy": "Orange",

        "fiolet": "Purple",

        "róż": "Pink",
        "roz": "Pink",

        "brąz": "Brown",
        "braz": "Brown",

        "tytan": "Titanium",
    }

    for polish_color, english_color in color_map.items():

        if polish_color in title_lower:

            return english_color

    # --------------------------------------------------------
    # English colors
    # --------------------------------------------------------

    if re.search(r"\bblack\b", title_lower):
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

def normalize_product_text(text):

    text = (
        str(text)
        .lower()
        .replace("\xa0", " ")
        .strip()
    )

    # Normalize Pro+
    text = re.sub(
        r"\bpro\s*\+",
        "pro+",
        text
    )

    # Replace common punctuation with spaces
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

    # Common abbreviation: "RM Note 17" == "Redmi Note 17"
    text = re.sub(r"\brm\b", "redmi", text)

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

    # ========================================================
    # SPECIAL CASE:
    # Xiaomi 17 family
    #
    # Ignore 5G naming difference for Xiaomi 17 family,
    # but NOT Xiaomi 17T family.
    # ========================================================

    xiaomi_17_family = (
        target_normalized.startswith("xiaomi 17")
        and
        not target_normalized.startswith("xiaomi 17t")
    )

    # ========================================================
    # SPECIAL CASE:
    # POCO X8 family
    #
    # Ignore 5G naming difference.
    # ========================================================

    poco_x8_family = (
        target_normalized.startswith("poco x8")
    )

    ignore_5g_difference = (
        xiaomi_17_family
        or
        poco_x8_family
    )

    # ========================================================
    # STYLUS / BUNDLE MATCHING
    #
    # Do not mix:
    #
    # Xiaomi Pad 8
    #
    # with:
    #
    # Xiaomi Pad 8 + Stylus
    # Xiaomi Pad 8 with Stylus
    # ========================================================

    target_has_stylus = bool(
        re.search(
            r"\bstylus\b",
            target_normalized
        )
    )

    title_has_stylus = bool(
        re.search(
            r"\bstylus\b",
            title_normalized
        )
    )

    if target_has_stylus != title_has_stylus:

        print(
            "Product mismatch: Stylus bundle does not match."
        )

        return False

    # ========================================================
    # 4G / LTE MATCHING
    #
    # IMPORTANT:
    #
    # Do NOT apply this rule globally.
    #
    # Only protect the base Redmi Pad 2 from being mixed
    # with Redmi Pad 2 4G / LTE versions.
    # ========================================================

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

    # ========================================================
    # 4G / 5G MATCHING  (deliberately NOT strict)
    #
    # A title that simply does not say "5G" is fine (many phones are
    # 5G-only). Only a real contradiction rejects the title, or - when
    # the Products sheet has both a 4G and a 5G version of the same
    # name - the 5G word decides. See matching.connectivity_ok().
    # ========================================================

    if ignore_5g_difference:

        print(
            "SPECIAL PRODUCT FAMILY: "
            "ignoring 5G difference."
        )

    else:

        connectivity_ok, connectivity_reason = matching.connectivity_ok(
            target_normalized,
            title_normalized,
            bool(product.get("has_5g_sibling", False))
        )

        if not connectivity_ok:

            print(
                "Product mismatch:",
                connectivity_reason
            )

            return False

    print(
        "CONNECTIVITY MATCH: YES"
    )

    # ========================================================
    # REMOVE CONNECTIVITY WORDS FOR PRODUCT NAME MATCHING
    #
    # We already checked them above.
    #
    # Remove:
    # - 5G
    # - 4G
    # - LTE
    # ========================================================

    title_core = re.sub(
        r"\b(?:5g|4g|lte)\b",
        "",
        title_normalized
    )

    target_core = re.sub(
        r"\b(?:5g|4g|lte)\b",
        "",
        target_normalized
    )

    title_core = re.sub(
        r"\s+",
        " ",
        title_core
    ).strip()

    target_core = re.sub(
        r"\s+",
        " ",
        target_core
    ).strip()

    title_tokens = title_core.split()

    target_tokens = target_core.split()

    # ========================================================
    # PRODUCT MODIFIERS
    #
    # Prevent shorter products from matching longer versions.
    #
    # Example:
    #
    # Redmi Pad 2
    #
    # must NOT match:
    #
    # Redmi Pad 2 Pro
    # Redmi Pad 2 Pro 5G
    # ========================================================

    product_modifiers = {
        "pro",
        "pro+",
        "ultra",
        "max",
        "lite",
        "plus",
    }

    # ========================================================
    # PRODUCT NAME MATCH
    #
    # The target words must appear TOGETHER and in order.
    # Only brand / category / connectivity words (smartfon, tablet,
    # xiaomi, 5g, lte, gb ...) may sit between them.
    #
    # OLD behaviour: any words could sit between them, so the target
    # "Redmi 17" also matched "Redmi NOTE 17 4G" (a different phone).
    #
    # A model word directly after the name (pro / ultra / max ...)
    # that the target does not have also rejects the title:
    # "Redmi Pad 2" must not match "Redmi Pad 2 Pro".
    # ========================================================

    matched, reason = matching.name_tokens_match(
        title_tokens,
        target_tokens,
        product_modifiers
    )

    if not matched:

        print(
            "Product mismatch:",
            reason
        )

        return False

    print(
        "PRODUCT NAME MATCH: YES"
    )

    return True


# ============================================================
# STORAGE NORMALIZATION
# ============================================================

def normalize_storage(value):

    if value is None:
        return None

    text = (
        str(value)
        .upper()
        .replace(" ", "")
    )

    # 1T / 1TB -> 1000
    match = re.fullmatch(
        r"(\d+)(T|TB)",
        text
    )

    if match:

        return str(
            int(match.group(1)) * 1000
        )

    # 512 / 512GB -> 512
    match = re.search(
        r"\d+",
        text
    )

    if match:

        return match.group()

    return None


# ============================================================
# MEMORY EXTRACTION
# ============================================================

def extract_memory(text):

    if not text:
        return None, None

    text = (
        str(text)
        .replace("\xa0", " ")
    )

    # --------------------------------------------------------
    # Supported formats:
    #
    # 12GB/512GB
    # 12 GB / 512 GB
    # 12GB 512GB
    # 12 GB 512 GB
    # 12/512
    #
    # Also:
    #
    # 12+512GB
    # 12 GB + 512 GB
    # 12GB+512GB
    # --------------------------------------------------------

    patterns = [

        # 12 GB / 512 GB
        r"\b(\d+)\s*GB\s*/\s*(\d+)\s*(GB|TB|T)\b",

        # 12 GB + 512 GB
        r"\b(\d+)\s*GB\s*\+\s*(\d+)\s*(GB|TB|T)\b",

        # 12+512GB
        r"\b(\d+)\s*\+\s*(\d+)\s*(GB|TB|T)\b",

        # 12GB 512GB
        r"\b(\d+)\s*GB\s+(\d+)\s*(GB|TB|T)\b",

        # 12 / 512 GB
        r"\b(\d+)\s*/\s*(\d+)\s*(GB|TB|T)\b",

        # 12/512
        r"\b(\d+)\s*/\s*(\d+)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        ram = match.group(1)

        storage_value = match.group(2)

        # Some patterns have a storage unit,
        # while 12/512 does not.
        storage_unit = (
            match.group(3)
            if len(match.groups()) >= 3
            else "GB"
        )

        if storage_unit:

            storage_unit = storage_unit.upper()

        else:

            storage_unit = "GB"

        if storage_unit in ("TB", "T"):

            storage = str(
                int(storage_value) * 1000
            )

        else:

            storage = storage_value

        return ram, storage

    return None, None


# ============================================================
# AVAILABILITY
# ============================================================

# LEGACY - no longer used. See matching.availability_from_card.
def get_availability(card_text):

    text = (
        str(card_text)
        .lower()
    )

    # --------------------------------------------------------
    # Explicitly unavailable
    # --------------------------------------------------------

    unavailable_phrases = [

        "niestety dostawa nie jest możliwa",

        "produkt niedostępny",

        "chwilowo niedostępny",

        "niedostępny online",

        "brak dostępności",

        "brak w magazynie",
    ]

    for phrase in unavailable_phrases:

        if phrase in text:

            return "Unavailable"

    # --------------------------------------------------------
    # Explicitly available
    # --------------------------------------------------------

    available_phrases = [

        "dostępny online",

        "available online",

        "place your order",

        "złóż zamówienie",

        "dostarczymy",

        "dostawa już jutro",

        "dodaj do koszyka",
    ]

    for phrase in available_phrases:

        if phrase in text:

            return "Available"

    return "Unknown"

# ============================================================
# SELLER / OFFICIAL MEDIA MARKT CHECK
# ============================================================

# LEGACY - no longer used. It assumed 'official' whenever no seller line
# was found. See matching.classify_seller for the replacement.
def is_official_media_markt_offer(card_text):

    if not card_text:

        return False

    text = (
        str(card_text)
        .lower()
        .replace("\xa0", " ")
    )

    # --------------------------------------------------------
    # Marketplace offer
    #
    # Example:
    #
    # Sprzedaż i wysyłka przez Deluxury
    #
    # These offers must NOT be used.
    # --------------------------------------------------------

    seller_match = re.search(
        r"sprzedaż\s+i\s+wysyłka\s+przez\s+([^\n]+)",
        text,
        re.IGNORECASE
    )

    if seller_match:

        seller = (
            seller_match
            .group(1)
            .strip()
        )

        print(
            "SELLER DETECTED:",
            seller
        )

        # ----------------------------------------------------
        # Accept only MediaMarkt as official seller
        # ----------------------------------------------------

        if "mediamarkt" in seller:

            print(
                "OFFICIAL MEDIA MARKT SELLER: YES"
            )

            return True

        print(
            "MARKETPLACE SELLER DETECTED:",
            seller
        )

        return False

    # --------------------------------------------------------
    # No marketplace seller information
    #
    # This is the normal official MediaMarkt offer format.
    # --------------------------------------------------------

    print(
        "NO MARKETPLACE SELLER DETECTED."
    )

    print(
        "ASSUMING OFFICIAL MEDIA MARKT OFFER."
    )

    return True

# ============================================================
# PRICE EXTRACTION
# ============================================================

# LEGACY - no longer used. It took the FIRST 'xxx,xx zł' in the card text,
# which can be a reference price or an instalment. See matching.first_price.
def extract_price(card):

    card_text = (
        card
        .inner_text()
        .strip()
    )

    # Examples:
    #
    # 399,99 zł
    # 799,00 zł
    # 1 299,00 zł
    # 1.299,00 zł

    price_matches = re.findall(
        r"\b\d{1,5}(?:[ .]\d{3})*[,.]\d{2}\s*zł\b",
        card_text,
        re.IGNORECASE
    )

    if not price_matches:

        return None

    return clean_price(
        price_matches[0]
    )


# ============================================================
# FALLBACK STORAGE FORMAT
# ============================================================

def format_storage(value):

    text = str(value).strip()

    if text.upper() in (
        "1T",
        "1TB"
    ):

        return "1 TB"

    if re.fullmatch(
        r"\d+",
        text
    ):

        return text + " GB"

    return text


# ============================================================
# PRODUCTS
# ============================================================
#
# HOW THIS SCRAPER DECIDES WHAT TO RECORD (MediaMarkt = MSH)
#
#   1. Find the product cards on the search page.
#   2. Keep only cards whose TITLE is the target model
#      (see matches_product + matching.name_tokens_match).
#   3. Keep only OFFICIAL MediaMarkt offers. A card that names a
#      third-party seller ("Sprzedaż i wysyłka przez XX") is dropped;
#      a card with no seller line is the normal official offer.
#   4. Keep only cards whose RAM/storage equals the target.
#   5. Read price from the real selling-price block only, never from
#      the crossed-out reference price ("Najniższa cena: ...") or the
#      instalment line ("Płać już od ... zł miesięcznie").
#   6. Read availability from MediaMarkt's own delivery status.
#
# Silent failures are turned into loud ones:
#   - 0 cards and no "no results" message  -> RuntimeError (ERROR row)
#   - anti-bot / access-denied page        -> RuntimeError, we stop

# MediaMarkt renamed data-test "mms-product-card" to
# "mms-cofr-product-card". The old selector then matched 0 cards and the
# scraper returned an empty list, so MSH came out blank. Accept both.
CARD_SELECTOR = (
    'article[data-test="mms-cofr-product-card"], '
    'article[data-test="mms-product-card"]'
)

BLOCKED_MARKERS = (
    "access denied",
    "captcha",
    "verify you are human",
    "just a moment",
    "unusual traffic",
    "are you a robot",
    "nie jesteś robotem",
)

NO_RESULT_MARKERS = (
    "nie znaleźliśmy",
    "brak wyników",
    "nie znaleziono",
)

# Runs inside the browser, once per card. Keeping the DOM reading in one
# small script (and the decisions in Python below) makes the decisions
# testable without a browser.
CARD_JS = """
el => {
  const q = s => el.querySelector(s);
  const titleEl = q('[data-test="product-list-item-link"]');
  const links = [...el.querySelectorAll('a')]
      .map(a => (a.innerText || '').trim()).filter(Boolean);

  const priceBox = q('[data-test="cofr-price mms-price"]');
  let priceTexts = [];
  if (priceBox) {
    const c = priceBox.cloneNode(true);
    // remove the crossed-out reference price, the instalment text and buttons
    c.querySelectorAll(
      '[data-test^="mms-strike-price"], ' +
      '[data-test="additional-info-normal-wrapper"], button'
    ).forEach(n => n.remove());
    priceTexts = [...c.querySelectorAll('span')]
      .map(s => (s.textContent || '').replace(/\\u00a0/g, ' ').trim())
      .filter(Boolean);
  }

  const del = el.querySelector('[data-test^="mms-cofr-delivery_"]');

  return {
    title: titleEl ? titleEl.innerText.trim() : '',
    links: links,
    hasPriceBox: !!priceBox,
    priceTexts: priceTexts,
    thirdParty: !!(q('[data-test="mms-third-party-provider-link"]') ||
                   q('a[href*="/marketplace/seller/"]')),
    delivery: del
      ? (del.getAttribute('data-test') || '').replace('mms-cofr-delivery_', '')
      : '',
    text: el.innerText || ''
  };
}
"""


def _wait_for_cards(page, timeout_ms=20000):
    """
    Wait until product cards are rendered.
    True  -> cards are present
    False -> the page says there are no results (legitimate empty result)
    Raises RuntimeError when the page is blocked or simply not understood,
    so the failure is visible instead of looking like "no data".
    """

    try:

        page.wait_for_selector(
            CARD_SELECTOR,
            timeout=timeout_ms
        )

        return True

    except Exception:

        pass

    try:

        body = (
            page.locator("body")
            .inner_text(timeout=5000)
            .lower()
        )

    except Exception:

        body = ""

    if any(marker in body for marker in BLOCKED_MARKERS):

        raise RuntimeError(
            "MediaMarkt is showing an anti-bot / access page. "
            "Stopped (not bypassing it)."
        )

    if (
        any(marker in body for marker in NO_RESULT_MARKERS)
        or re.search(r"wynik wyszukiwania dla:.*\(0\)", body)
    ):

        print("MediaMarkt reports no search results.")

        return False

    raise RuntimeError(
        "MediaMarkt: no product cards found and no 'no results' message. "
        "The page did not load, or the card selector changed again "
        f"(CARD_SELECTOR = {CARD_SELECTOR})."
    )


def _matching_title(info, product):
    """First title/link text of the card that is the target product."""

    candidates = [info.get("title") or ""]

    candidates += list(info.get("links") or [])

    for text in candidates:

        if text and matches_product(text, product):

            return text

    return ""


def build_results(infos, product, read_errors=0):
    """
    Pure decision logic: list of card dicts (see CARD_JS) -> result rows.
    """

    results = []

    target_ram = re.sub(
        r"\D",
        "",
        str(product["ram"])
    )

    target_storage = normalize_storage(
        product["storage"]
    )

    print("TARGET PRODUCT:", product["name"])
    print("TARGET RAM:", target_ram)
    print("TARGET STORAGE:", target_storage, "GB")

    # --------------------------------------------------------
    # Pass 1: title + seller
    # --------------------------------------------------------

    official = []

    for i, info in enumerate(infos):

        print()
        print("=" * 60)
        print("MEDIAMARKT CARD", i)
        print("=" * 60)

        title = _matching_title(info, product)

        if not title:

            print("Not the target product.")

            continue

        card_text = info.get("text") or ""

        verdict, detail = matching.classify_seller(
            card_text,
            info.get("thirdParty")
        )

        print("TITLE:", title)
        print("SELLER VERDICT:", verdict, "-", detail)

        if verdict == "marketplace":

            print("Skipping marketplace offer.")

            continue

        ram, storage = extract_memory(title)

        if ram is None:

            ram, storage = extract_memory(card_text)

        official.append((i, title, info, ram, storage))

    # --------------------------------------------------------
    # Pass 2: memory + price + availability (official only)
    # --------------------------------------------------------

    for i, title, info, ram, storage in official:

        print()
        print("-" * 60)
        print("OFFICIAL CARD", i, "-", title)

        if ram is None:

            # Some cards do not display memory. Only safe when this is
            # the single official card for the target product.
            if len(official) == 1:

                print(
                    "MEMORY NOT DISPLAYED. SAFE FALLBACK: "
                    "single official matching card."
                )

                ram = target_ram

                storage = target_storage

            else:

                print(
                    "RAM/storage not found and fallback is not safe."
                )

                continue

        actual_ram = re.sub(r"\D", "", str(ram))

        actual_storage = normalize_storage(storage)

        print("ACTUAL RAM/STORAGE:", actual_ram, "/", actual_storage)

        if (
            actual_ram != target_ram
            or actual_storage != target_storage
        ):

            print("RAM/storage does not match.")

            continue

        card_text = info.get("text") or ""

        if info.get("priceTexts"):

            price = matching.first_price(
                info["priceTexts"]
            )

        elif not info.get("hasPriceBox"):

            price = matching.price_from_card_text(
                card_text
            )

        else:

            price = None

        availability = matching.availability_from_card(
            info.get("delivery"),
            card_text
        )

        color = get_color(title)

        if availability == "Available" and price is None:

            print(
                "WARNING: available but no price could be read."
            )

        result = {

            "product_name": product["name"],

            "variant": color,

            "ram": actual_ram,

            "storage": actual_storage,

            "price": price,

            "availability": availability,
        }

        print("RESULT:", result)

        results.append(result)

    # --------------------------------------------------------
    # Not found
    # --------------------------------------------------------

    if not results:

        if read_errors:

            raise RuntimeError(
                f"{read_errors} product card(s) could not be read, "
                "so 'not found' cannot be trusted."
            )

        print()
        print("=" * 60)
        print("Target product not found as an official MediaMarkt offer.")
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

    print()
    print("=" * 60)
    print("MEDIAMARKT RESULTS:", len(results))
    print("=" * 60)

    for result in results:

        print(result)

    return results


def get_products(page, product):

    print("Waiting for MediaMarkt products...")

    infos = []

    read_errors = 0

    if _wait_for_cards(page):

        cards = page.locator(CARD_SELECTOR)

        count = cards.count()

        print("MediaMarkt product cards:", count)

        for i in range(count):

            try:

                infos.append(
                    cards.nth(i).evaluate(CARD_JS)
                )

            except Exception as e:

                read_errors += 1

                print("ERROR READING CARD:", i, str(e))

    return build_results(
        infos,
        product,
        read_errors
    )


# ============================================================
# UNIFIED SCRAPER INTERFACE
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