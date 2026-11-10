#NOT WORKING FOR NOW!!
#EURO BLOCKS ACCESS WITH ANTI BOTS

import re
import requests
from bs4 import BeautifulSoup


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = (
        str(text)
        .lower()
        .replace("\xa0", " ")
    )

    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_storage(value):

    if value is None:
        return None

    text = (
        str(value)
        .upper()
        .replace(" ", "")
    )

    # 1TB / 1T
    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)(TB|T)",
        text
    )

    if match:

        return str(
            int(float(match.group(1)) * 1000)
        )

    # 64 / 64GB
    match = re.search(
        r"\d+",
        text
    )

    if match:

        return match.group()

    return None


# ============================================================
# PRICE
# ============================================================

def clean_price(text):

    if not text:
        return None

    text = (
        str(text)
        .replace("\xa0", " ")
        .strip()
    )

    # Examples:
    #
    # 449 zł
    # 449,00 zł
    # 1 299,00 zł
    # 1.299,00 zł

    match = re.search(
        r"(\d[\d\s.]*(?:,\d{1,2})?)\s*zł",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    value = match.group(1)

    value = value.replace(" ", "")

    # Polish format:
    # 1.299,00 -> 1299.00

    if "," in value:

        value = value.replace(".", "")
        value = value.replace(",", ".")

    else:

        # 1299.00
        # 449

        # If multiple dots exist, treat them as
        # thousand separators.

        if value.count(".") > 1:

            value = value.replace(".", "")

    try:

        return float(value)

    except ValueError:

        return None


# ============================================================
# COLOR
# ============================================================

def get_color(title):

    title_lower = normalize_text(title)

    colors = {

        "czarny": "Black",
        "czarna": "Black",
        "czarne": "Black",
        "czarn": "Black",

        "zielony": "Green",
        "zielona": "Green",
        "zielone": "Green",
        "zielon": "Green",

        "niebieski": "Blue",
        "niebieska": "Blue",
        "niebieskie": "Blue",
        "niebiesk": "Blue",

        "biały": "White",
        "bialy": "White",
        "biała": "White",
        "biala": "White",

        "szary": "Grey",
        "szara": "Grey",
        "szare": "Grey",
        "szar": "Grey",

        "srebrny": "Silver",
        "srebrna": "Silver",
        "srebrne": "Silver",
        "srebr": "Silver",

        "złoty": "Gold",
        "zloty": "Gold",
        "złota": "Gold",
        "zlota": "Gold",
        "złot": "Gold",
        "zlot": "Gold",

        "fioletowy": "Purple",
        "fioletowa": "Purple",
        "fiolet": "Purple",

        "różowy": "Pink",
        "rozowy": "Pink",
        "różowa": "Pink",
        "rozowa": "Pink",
        "róż": "Pink",
        "roz": "Pink",

        "czerwony": "Red",
        "czerwona": "Red",
        "czerw": "Red",

        "brązowy": "Brown",
        "brazowy": "Brown",
        "brąz": "Brown",
        "braz": "Brown",

        "tytanowy": "Titanium",
        "tytan": "Titanium",
    }

    for polish, english in colors.items():

        if polish in title_lower:

            return english

    # English

    english_colors = {

        "black": "Black",
        "green": "Green",
        "blue": "Blue",
        "white": "White",
        "grey": "Grey",
        "gray": "Grey",
        "silver": "Silver",
        "gold": "Gold",
        "purple": "Purple",
        "pink": "Pink",
        "red": "Red",
        "brown": "Brown",
        "titanium": "Titanium",
    }

    for english, result in english_colors.items():

        if re.search(
            rf"\b{re.escape(english)}\b",
            title_lower
        ):

            return result

    return "Unknown"


# ============================================================
# PRODUCT MATCHING
# ============================================================

def normalize_product_text(text):

    text = normalize_text(text)

    # Pro+
    text = re.sub(
        r"\bpro\s*\+",
        "pro+",
        text
    )

    # punctuation
    text = re.sub(
        r"[/(),;:_\-]+",
        " ",
        text
    )

    # Keep letters/numbers/+
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
    # Xiaomi 17 family
    # --------------------------------------------------------

    xiaomi_17_family = (
        target_normalized.startswith("xiaomi 17")
        and
        not target_normalized.startswith("xiaomi 17t")
    )

    # --------------------------------------------------------
    # POCO X8 family
    # --------------------------------------------------------

    poco_x8_family = (
        target_normalized.startswith("poco x8")
    )

    ignore_5g_difference = (
        xiaomi_17_family
        or
        poco_x8_family
    )

    # --------------------------------------------------------
    # STYLUS
    # --------------------------------------------------------

    target_has_stylus = bool(
        re.search(
            r"\b(?:stylus|rysik)\b",
            target_normalized
        )
    )

    title_has_stylus = bool(
        re.search(
            r"\b(?:stylus|rysik)\b",
            title_normalized
        )
    )

    if target_has_stylus != title_has_stylus:

        print(
            "Product mismatch: Stylus/Rysik bundle."
        )

        return False

    # --------------------------------------------------------
    # REDMI PAD 2 4G / LTE SPECIAL RULE
    #
    # IMPORTANT:
    # This is NOT GLOBAL.
    #
    # Only base Redmi Pad 2 is protected here.
    # --------------------------------------------------------

    is_base_redmi_pad_2 = (
        target_normalized == "redmi pad 2"
    )

    if is_base_redmi_pad_2:

        target_has_lte = bool(
            re.search(
                r"\b(?:4g|lte)\b",
                target_normalized
            )
        )

        title_has_lte = bool(
            re.search(
                r"\b(?:4g|lte)\b",
                title_normalized
            )
        )

        if target_has_lte != title_has_lte:

            print(
                "Product mismatch: Redmi Pad 2 "
                "4G/LTE version."
            )

            return False

    # --------------------------------------------------------
    # 5G
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

    if not ignore_5g_difference:

        if target_has_5g != title_has_5g:

            print(
                "Product mismatch: 5G version."
            )

            return False

    else:

        print(
            "SPECIAL PRODUCT FAMILY: "
            "ignoring 5G difference."
        )

    # --------------------------------------------------------
    # Remove connectivity labels
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Model modifiers
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
    # Ordered token matching
    # --------------------------------------------------------

    position = 0
    matched_positions = []

    for target_token in target_tokens:

        found = False

        while position < len(title_tokens):

            if title_tokens[position] == target_token:

                matched_positions.append(
                    position
                )

                position += 1

                found = True

                break

            position += 1

        if not found:

            print(
                "Product name mismatch."
            )

            return False

    # --------------------------------------------------------
    # Prevent:
    #
    # Redmi Pad 2
    #
    # matching:
    #
    # Redmi Pad 2 Pro
    # --------------------------------------------------------

    if matched_positions:

        last_position = matched_positions[-1]

        if last_position + 1 < len(title_tokens):

            next_token = title_tokens[
                last_position + 1
            ]

            if (
                next_token in product_modifiers
                and
                next_token not in target_tokens
            ):

                print(
                    "Product mismatch: additional "
                    f"model modifier '{next_token}'."
                )

                return False

    print(
        "PRODUCT NAME MATCH: YES"
    )

    return True


# ============================================================
# MEMORY
# ============================================================

def extract_memory(text):

    if not text:
        return None, None

    text = (
        str(text)
        .replace("\xa0", " ")
    )

    patterns = [

        # 4 GB / 64 GB
        r"\b(\d+)\s*GB\s*/\s*(\d+)\s*(GB|TB|T)\b",

        # 4 GB + 64 GB
        r"\b(\d+)\s*GB\s*\+\s*(\d+)\s*(GB|TB|T)\b",

        # 4+64GB
        r"\b(\d+)\s*\+\s*(\d+)\s*(GB|TB|T)\b",

        # 4GB 64GB
        r"\b(\d+)\s*GB\s+(\d+)\s*(GB|TB|T)\b",

        # 4/64GB
        r"\b(\d+)\s*/\s*(\d+)\s*(GB|TB|T)\b",

        # 4/64
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

        if len(match.groups()) >= 3:

            storage_unit = (
                match.group(3)
                or
                "GB"
            ).upper()

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
# EURO ANTI-BOT DETECTION
# ============================================================

def is_euro_blocked(page):

    try:

        title = normalize_text(
            page.title()
        )

    except Exception:

        title = ""

    try:

        body = normalize_text(
            page.locator("body").inner_text()
        )

    except Exception:

        body = ""

    print(
        "PAGE TITLE:",
        title
    )

    # Known EURO/OLEOLE block page

    blocked_phrases = [

        "rtv euro agd - blokada",

        "oleole! - blokada",

        "twoje żądanie zostało zablokowane",

        "twoje zadanie zostalo zablokowane",

    ]

    for phrase in blocked_phrases:

        if phrase in title or phrase in body:

            return True

    return False


# ============================================================
# SEARCH-ENGINE FALLBACK
# ============================================================

def search_euro_index(product):
    """
    Search publicly indexed EURO pages.

    This does NOT bypass EURO's anti-bot system.
    It only reads publicly available search-engine results.
    """

    print()
    print("=" * 60)
    print("EURO INDEX FALLBACK")
    print("=" * 60)

    queries = [
        f'site:euro.com.pl "{product["name"]}"',
        f'site:euro.com.pl "{product["name"]}" "{product["ram"]}/{product["storage"]}"',
        f'site:euro.com.pl "{product["name"]}" "{product["storage"]}GB"',
    ]

    # --------------------------------------------------------
    # Build possible model/product-code query
    # --------------------------------------------------------

    model = str(product.get("model", "")).strip()

    if model:
        queries.append(
            f'site:euro.com.pl "{model}"'
        )

    all_candidates = []
    seen_urls = set()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/153.0 Safari/537.36"
        ),
        "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
    }

    search_url = "https://www.bing.com/search"

    for query in queries:

        print()
        print("-" * 60)
        print("SEARCH QUERY:")
        print(query)

        try:

            response = requests.get(
                search_url,
                params={
                    "q": query,
                    "count": 20,
                },
                headers=headers,
                timeout=15,
            )

        except Exception as e:

            print(
                "SEARCH REQUEST ERROR:",
                e
            )

            continue

        print(
            "SEARCH STATUS:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "Search engine request failed."
            )

            continue

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        query_candidates = []

        # ====================================================
        # METHOD 1
        # Standard Bing result blocks
        # ====================================================

        for result in soup.select("li.b_algo"):

            link = result.select_one("h2 a")

            if link is None:
                continue

            href = link.get("href", "")

            if not href:
                continue

            title = link.get_text(
                " ",
                strip=True
            )

            snippet_element = result.select_one(
                ".b_caption"
            )

            snippet = ""

            if snippet_element:

                snippet = snippet_element.get_text(
                    " ",
                    strip=True
                )

            query_candidates.append({
                "title": title,
                "url": href,
                "snippet": snippet,
            })

        # ====================================================
        # METHOD 2
        # Fallback: inspect ALL anchors
        #
        # Bing sometimes changes its result markup.
        # ====================================================

        if not query_candidates:

            print(
                "Standard Bing selector found nothing."
            )

            print(
                "Trying generic EURO link extraction..."
            )

            for link in soup.find_all("a"):

                href = link.get("href", "")

                if not href:
                    continue

                href_lower = href.lower()

                if "euro.com.pl" not in href_lower:
                    continue

                # Ignore search/navigation URLs
                if (
                    "bing.com" in href_lower
                    or
                    href_lower.startswith("javascript:")
                ):
                    continue

                title = link.get_text(
                    " ",
                    strip=True
                )

                if not title:
                    continue

                # Get nearby parent text as a rough snippet
                parent = link.parent

                snippet = ""

                if parent:

                    snippet = parent.get_text(
                        " ",
                        strip=True
                    )

                query_candidates.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                })

        # ====================================================
        # Deduplicate candidates
        # ====================================================

        for candidate in query_candidates:

            href = candidate["url"]

            # Normalize tracking parameters where possible
            href = href.split("?")[0]

            if href in seen_urls:
                continue

            seen_urls.add(href)

            candidate["url"] = href

            all_candidates.append(
                candidate
            )

        print(
            "EURO CANDIDATES FROM THIS QUERY:",
            len(query_candidates)
        )

    # ========================================================
    # Final output
    # ========================================================

    print()
    print(
        "TOTAL UNIQUE EURO CANDIDATES:",
        len(all_candidates)
    )

    for i, candidate in enumerate(
        all_candidates,
        start=1
    ):

        print()
        print(
            f"[{i}] TITLE:",
            candidate["title"]
        )

        print(
            "URL:",
            candidate["url"]
        )

        print(
            "SNIPPET:",
            candidate["snippet"][:500]
        )

    return all_candidates


# ============================================================
# PARSE INDEXED RESULT
# ============================================================

def parse_indexed_result(
    candidate,
    product
):

    title = candidate["title"]

    snippet = candidate["snippet"]

    combined = (
        title
        + " "
        + snippet
    )

    print()
    print(
        "CHECKING INDEXED RESULT:"
    )

    print(
        combined
    )

    # --------------------------------------------------------
    # Product matching
    # --------------------------------------------------------

    if not matches_product(
        title,
        product
    ):

        # Sometimes the title is shortened.
        # Try the complete snippet too.

        if not matches_product(
            combined,
            product
        ):

            print(
                "Indexed product does not match."
            )

            return None

    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    ram, storage = extract_memory(
        combined
    )

    if ram is None:

        print(
            "Indexed result: RAM/storage not found."
        )

        return None

    target_ram = re.sub(
        r"\D",
        "",
        str(product["ram"])
    )

    target_storage = normalize_storage(
        product["storage"]
    )

    actual_storage = normalize_storage(
        storage
    )

    if (
        ram != target_ram
        or
        actual_storage != target_storage
    ):

        print(
            "Indexed result memory mismatch."
        )

        return None

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    price = clean_price(
        combined
    )

    print(
        "INDEXED PRICE:",
        price
    )

    # --------------------------------------------------------
    # Color
    # --------------------------------------------------------

    color = get_color(
        combined
    )

    print(
        "INDEXED COLOR:",
        color
    )

    # --------------------------------------------------------
    # Availability
    # --------------------------------------------------------

    text_lower = normalize_text(
        combined
    )

    if any(
        phrase in text_lower
        for phrase in [
            "do koszyka",
            "dostępny online",
            "dostepny online",
            "najwcześniej u ciebie",
            "najwczesniej u ciebie",
        ]
    ):

        availability = "Available"

    elif any(
        phrase in text_lower
        for phrase in [
            "produkt niedostępny",
            "produkt niedostepny",
            "chwilowo niedostępny",
            "chwilowo niedostepny",
            "brak w magazynie",
        ]
    ):

        availability = "Unavailable"

    else:

        availability = "Unknown"

    return {

        "product_name":
            product["name"],

        "variant":
            color,

        "ram":
            ram + " GB",

        "storage":
            actual_storage + " GB",

        "price":
            price,

        "availability":
            availability,

        "source_status":
            "indexed",

        "source_url":
            candidate["url"],
    }


# ============================================================
# INDEX FALLBACK
# ============================================================

def get_index_fallback(product):

    candidates = search_euro_index(
        product
    )

    if not candidates:

        print(
            "No indexed EURO candidates found."
        )

        return []

    results = []

    for candidate in candidates:

        result = parse_indexed_result(
            candidate,
            product
        )

        if result is None:

            continue

        results.append(
            result
        )

    return results


# ============================================================
# DIRECT EURO SCRAPER
# ============================================================

def get_products(page, product):

    print(
        "Waiting for EURO products..."
    )

    page.wait_for_timeout(
        3000
    )

    # --------------------------------------------------------
    # Detect anti-bot block
    # --------------------------------------------------------

    if is_euro_blocked(page):

        print()
        print(
            "EURO ANTI-BOT BLOCK DETECTED."
        )

        print(
            "Trying indexed-data fallback..."
        )

        fallback_results = get_index_fallback(
            product
        )

        if fallback_results:

            return fallback_results

        print(
            "Indexed fallback also returned no result."
        )

        return [{
            "product_name":
                product["name"],

            "variant":
                "Unknown",

            "ram":
                str(product["ram"]) + " GB",

            "storage":
                normalize_storage(
                    product["storage"]
                ) + " GB",

            "price":
                None,

            "availability":
                "Blocked",

            "source_status":
                "blocked",

            "source_url":
                None,
        }]

    # --------------------------------------------------------
    # Normal direct-page scraping
    # --------------------------------------------------------

    body = page.locator(
        "body"
    ).inner_text()

    if (
        product["name"].lower()
        not in body.lower()
    ):

        print(
            "Target product not found on EURO page."
        )

        return []

    cards = page.locator(
        "[data-productid]"
    )

    print(
        "EURO product containers:",
        cards.count()
    )

    target_ram = re.sub(
        r"\D",
        "",
        str(product["ram"])
    )

    target_storage = normalize_storage(
        product["storage"]
    )

    results = []

    for i in range(cards.count()):

        card = cards.nth(i)

        try:

            card_text = card.inner_text()

        except Exception:

            continue

        title_element = card.locator(
            "a"
        ).filter(
            has_text=re.compile(
                re.escape(
                    product["name"]
                ),
                re.IGNORECASE
            )
        ).first

        if title_element.count() == 0:

            continue

        title = (
            title_element
            .inner_text()
            .strip()
        )

        if not matches_product(
            title,
            product
        ):

            continue

        ram, storage = extract_memory(
            title
        )

        if ram is None:

            ram, storage = extract_memory(
                card_text
            )

        if ram is None:

            continue

        actual_storage = normalize_storage(
            storage
        )

        if (
            ram != target_ram
            or
            actual_storage != target_storage
        ):

            continue

        color = get_color(
            title
        )

        price = clean_price(
            card_text
        )

        text_lower = normalize_text(
            card_text
        )

        if any(
            phrase in text_lower
            for phrase in [
                "do koszyka",
                "dostępny",
                "dostepny",
                "najwcześniej u ciebie",
                "najwczesniej u ciebie",
            ]
        ):

            availability = "Available"

        elif any(
            phrase in text_lower
            for phrase in [
                "produkt niedostępny",
                "produkt niedostepny",
                "chwilowo niedostępny",
                "chwilowo niedostepny",
            ]
        ):

            availability = "Unavailable"

        else:

            availability = "Unknown"

        results.append({

            "product_name":
                product["name"],

            "variant":
                color,

            "ram":
                ram + " GB",

            "storage":
                actual_storage + " GB",

            "price":
                price,

            "availability":
                availability,

            "source_status":
                "live",

            "source_url":
                page.url,
        })

    return results


# ============================================================
# UNIFIED INTERFACE
# ============================================================

def get_price(page, product=None):

    if product is None:

        return None

    return get_products(
        page,
        product
    )