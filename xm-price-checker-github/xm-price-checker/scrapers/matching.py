"""
Shared, pure-Python matching helpers (no Playwright, no I/O) so they can be
unit-tested offline and reused by every scraper.

Why this file exists
--------------------
The old per-scraper logic had these silent failure modes:

1. Product-name matching allowed ARBITRARY words between the target words, so
   target "Redmi 17" matched "Redmi NOTE 17 4G" (a different phone).
2. The price was "the first 'xxx,xx zł' found in the card text", which can be a
   crossed-out reference price ("Najniższa cena: 4999,– zł") or an instalment
   ("Płać już od 26,08 zł miesięcznie").

Everything below replaces those guesses with explicit, testable rules.
"""

import json
import os
import re
import unicodedata

# ------------------------------------------------------------------
# 1. PRODUCT NAME MATCHING
# ------------------------------------------------------------------

# Words that may sit BETWEEN two words of the target name without changing
# which product it is (brand / category / connectivity noise).
# Anything else between the words (e.g. "note", "pro", "ultra") means the
# title is a different model and must NOT match.
GAP_OK_WORDS = {
    "smartfon", "telefon", "tablet", "xiaomi",
    "5g", "4g", "lte", "nfc", "dual", "sim",
    "gb", "tb",
}

# Words that, when they directly FOLLOW the target name, turn it into a
# different (bigger) model: "Redmi Pad 2" must not match "Redmi Pad 2 Pro".
DEFAULT_MODIFIERS = {"pro", "pro+", "ultra", "max", "lite", "plus"}


# ------------------------------------------------------------------
# 1b. CONNECTIVITY (4G / 5G) - only reject on a REAL conflict
# ------------------------------------------------------------------

def connectivity_ok(target_text, title_text, has_5g_sibling=False):
    """
    Return (ok: bool, reason: str).  Both texts are already normalised
    (lower case, words separated by spaces).

    A missing "5G" is NOT a mismatch: many phones are 5G-only and shops
    often leave the word out.  The title is rejected only when it clearly
    says the opposite:

      * target is 5G, title says 4G/LTE (and not 5G)
      * target is 4G/LTE, title says 5G

    Extra strictness only when the Products sheet really contains BOTH a
    4G and a 5G version of the same name (has_5g_sibling), e.g.
    "Redmi Note 17" and "Redmi Note 17 5G": then the 5G word decides.
    """

    t5 = bool(re.search(r"\b5g\b", target_text))
    c5 = bool(re.search(r"\b5g\b", title_text))
    t4 = bool(re.search(r"\b(?:4g|lte)\b", target_text))
    c4 = bool(re.search(r"\b(?:4g|lte)\b", title_text))

    if t5 and c4 and not c5:
        return False, "target is 5G but the title says 4G/LTE"

    if t4 and not t5 and c5:
        return False, "target is 4G/LTE but the title says 5G"

    if has_5g_sibling:

        if t5 and not c5:
            return False, (
                "a 4G and a 5G version both exist and the title does not "
                "say 5G"
            )

        if not t5 and c5:
            return False, (
                "a 4G and a 5G version both exist and the title says 5G"
            )

    return True, ""


def name_tokens_match(title_tokens, target_tokens, modifiers=DEFAULT_MODIFIERS):
    """
    Return (matched: bool, reason: str).

    The target tokens must appear in order and CONTIGUOUSLY in the title,
    except that words from GAP_OK_WORDS may be skipped between them.
    The word right after the last matched token must not be a model modifier
    (pro / ultra / max ...) that the target itself does not contain.
    """

    if not target_tokens:
        return False, "empty target name"

    reason = "target name words not found together in the title"

    for start, token in enumerate(title_tokens):

        if token != target_tokens[0]:
            continue

        position = start
        last = start
        ok = True

        for target_token in target_tokens[1:]:

            j = position + 1

            while (
                j < len(title_tokens)
                and title_tokens[j] != target_token
                and title_tokens[j] in GAP_OK_WORDS
            ):
                j += 1

            if j < len(title_tokens) and title_tokens[j] == target_token:
                position = j
                last = j
            else:
                ok = False
                break

        if not ok:
            continue

        following = (
            title_tokens[last + 1]
            if last + 1 < len(title_tokens)
            else None
        )

        if (
            following in modifiers
            and following not in target_tokens
        ):
            reason = (
                f"title has extra model word '{following}' "
                "that the target does not have"
            )
            continue

        return True, ""

    return False, reason


# ------------------------------------------------------------------
# 2. PRICE PARSING
# ------------------------------------------------------------------

# Accepts: "3739,– zł"  "3739,00zł"  "1 299,00 zł"  "1.299,00 zł"
# Rejects: percentages, "od 26,08 zł miesięcznie" (extra words), bare numbers.
_PRICE_RE = re.compile(
    r"^\s*(\d{1,3}(?:[ .]\d{3})+|\d+)\s*,\s*(\d{2}|[–—-])\s*zł\s*$",
    re.IGNORECASE,
)


def parse_price_text(text):
    """Parse one price string into a float, or None if it is not a bare price."""

    if text is None:
        return None

    cleaned = (
        str(text)
        .replace("\xa0", " ")
        .replace(" ", " ")
        .strip()
    )

    match = _PRICE_RE.match(cleaned)

    if not match:
        return None

    whole = re.sub(r"[ .]", "", match.group(1))

    decimals = match.group(2)

    if not decimals.isdigit():
        decimals = "00"

    return float(f"{whole}.{decimals}")


def first_price(price_texts):
    """First text in the list that is a bare price (see parse_price_text)."""

    for text in price_texts or []:

        value = parse_price_text(text)

        if value is not None:
            return value

    return None


# Lines that contain a price-looking number but are NOT the selling price.
_NOT_SELLING_PRICE_HINTS = (
    "najniższa cena",     # Omnibus "lowest price in last 30 days" (reference)
    "miesięcznie",        # instalment
    "miesiąc",
    "rat",                # raty / rata
    "odnowion",           # "refurbished offers from ..."
    "używan",
    "outlet",
)

_LOOSE_PRICE_RE = re.compile(
    r"(\d{1,3}(?:[ .]\d{3})+|\d+)\s*,\s*(\d{2}|[–—-])\s*zł",
    re.IGNORECASE,
)


def price_from_card_text(card_text):
    """
    Fallback when the DOM price block is not available: scan the card text
    line by line, skipping reference / instalment / refurbished lines.

    MediaMarkt prints every price twice ("4999,– zł" then a hidden
    "4999,00zł"), so after skipping "Najniższa cena: 4999,– zł" the
    duplicate 4999 on the next line is skipped as well.
    """

    ignored_values = set()

    lines = str(card_text).replace("\xa0", " ").split("\n")

    # pass 1: remember every reference/instalment/refurbished amount
    for line in lines:

        lowered = line.lower()

        if any(hint in lowered for hint in _NOT_SELLING_PRICE_HINTS):

            for found in _LOOSE_PRICE_RE.finditer(line):

                value = parse_price_text(found.group(0))

                if value is not None:
                    ignored_values.add(value)

    # pass 2: first remaining price
    for line in lines:

        lowered = line.lower()

        if any(hint in lowered for hint in _NOT_SELLING_PRICE_HINTS):
            continue

        match = _LOOSE_PRICE_RE.search(line)

        if not match:
            continue

        value = parse_price_text(match.group(0))

        if value is not None and value not in ignored_values:
            return value

    return None


# ------------------------------------------------------------------
# 3. SELLER: OFFICIAL vs MARKETPLACE vs UNCERTAIN
# ------------------------------------------------------------------

_SELLER_RE = re.compile(
    r"sprzedaż\s+i\s+wysyłka\s+przez\s+([^\n|]+)",
    re.IGNORECASE,
)


def classify_seller(card_text, third_party_link=False):
    """
    Decide who sells the offer on a MediaMarkt card (original rule).

    Returns (verdict, detail), verdict being "official" or "marketplace":

      "marketplace" - a third-party seller is named ("Sprzedaż i wysyłka
                      przez XX"; the card also links to that seller's page).
                      Never used.
      "official"    - everything else, including a card with no seller line
                      (the normal format of an official MediaMarkt offer).
    """

    text = str(card_text or "").replace("\xa0", " ")

    match = _SELLER_RE.search(text)

    if match:

        seller = match.group(1).strip()

        # "Sprzedaż i wysyłka przez MediaMarkt" would still be official.
        if "mediamarkt" in seller.lower().replace(" ", ""):
            return "official", f"seller line names MediaMarkt ({seller})"

        return "marketplace", seller

    if third_party_link:
        return "marketplace", "link to marketplace seller page"

    return "official", "no third-party seller named"


# ------------------------------------------------------------------
# 4. AVAILABILITY
# ------------------------------------------------------------------

def availability_from_card(delivery_status, card_text):
    """
    delivery_status comes from data-test="mms-cofr-delivery_<STATUS>".
    Falls back to the visible Polish phrases.
    """

    status = str(delivery_status or "").upper()

    if status == "AVAILABLE":
        return "Available"

    if status == "NOT_AVAILABLE":
        return "Unavailable"

    text = str(card_text or "").lower().replace("\xa0", " ")

    if "niestety dostawa nie jest możliwa" in text:
        return "Unavailable"

    for phrase in (
        "produkt niedostępny",
        "chwilowo niedostępny",
        "niedostępny online",
        "brak dostępności",
        "brak w magazynie",
    ):
        if phrase in text:
            return "Unavailable"

    for phrase in (
        "dostępny online",
        "dodaj do koszyka",
        "złóż zamówienie",
    ):
        if phrase in text:
            return "Available"

    return "Unknown"


# ============================================================
# AVAILABILITY (shared by every text-based scraper)
# ============================================================
#
# Retailer pages change their wording. Rules that keep this robust:
#   * accents are removed first (dostepny == dostępny, Wysyłamy == wysylamy)
#   * UNAVAILABLE markers are tested first, because "niedostepny"
#     contains "dostepny"
#   * matching is by short stems, not whole sentences
#   * anything not recognised stays "Unknown" - and price_checks.py raises a
#     HIGH 'layout-changed' alarm when too many cards of one site are Unknown

def ascii_text(text):

    text = unicodedata.normalize("NFKD", str(text).lower())

    text = "".join(c for c in text if not unicodedata.combining(c))

    text = text.replace("ł", "l").replace(" ", " ")

    return re.sub(r"\s+", " ", text)


UNAVAILABLE_MARKERS = (
    "niedostepn",              # (produkt / chwilowo / tymczasowo) niedostepny
    "nie jest dostepn",
    "brak w magazynie",
    "brak towaru",
    "brak produktu",
    "brak na stanie",
    "chwilowo brak",
    "powiadom o dostepnosci",
    "powiadom mnie",
    "zapytaj o dostepnosc",
    "czekamy na dostaw",       # back-order (decided: treat as unavailable)
    "oczekuje na dostaw",
    "wyprzedan",
    "wycofan",
    "out of stock",
    "sold out",
    "unavailable",
)

AVAILABLE_MARKERS = (
    "dodaj do koszyka",
    "do koszyka",
    "kup teraz",
    "dostepny",
    "dostepna",
    "dostepne",
    "wysylamy najczesciej",
    "wysylka najczesciej",
    "wysylamy z salonu",
    "wysylamy w",
    "w magazynie",
    "na stanie",
    "ostatnie sztuki",
    "najwczesniej u ciebie",
    "in stock",
    "available",
)


MARKERS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "availability_markers.json",
)

UNKNOWN_LOG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "unknown_availability.log",
)


def _extra_markers():

    """Words the user added in availability_markers.json (optional file)."""

    try:
        with open(MARKERS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return (), ()

    def clean(items):
        return tuple(ascii_text(x).strip() for x in items or [] if str(x).strip())

    return clean(data.get("unavailable")), clean(data.get("available"))


def _log_unknown(card_text):

    """Remember the wording that was not recognised (for the check report)."""

    try:
        tail = re.sub(r"\s+", " ", str(card_text)).strip()[-220:]
        with open(UNKNOWN_LOG, "a", encoding="utf-8") as f:
            f.write(tail + "\n")
    except OSError:
        pass


def classify_availability(card_text):

    """Card text -> 'Available' / 'Unavailable' / 'Unknown'."""

    if not card_text:
        return "Unknown"

    text = ascii_text(card_text)

    extra_un, extra_av = _extra_markers()

    if any(m in text for m in UNAVAILABLE_MARKERS + extra_un):
        return "Unavailable"

    if any(m in text for m in AVAILABLE_MARKERS + extra_av):
        return "Available"

    _log_unknown(card_text)

    return "Unknown"


# ============================================================
# COLOUR (shared fallback used by every scraper's get_color)
# ============================================================
#
# Each scraper has its own colour list. When that list returns 'Unknown',
# this wider list (English + Polish + Xiaomi marketing names) is tried, so a
# new colour name such as 'Cloud Blush' is not left blank in Results.

COLOUR_WORDS = {
    "Black": ("midnight black", "graphite black", "obsidian black", "jet black",
              "black", "czarny", "czarna", "czarne", "grafitowy", "grafitowa",
              "onyx", "midnight", "graphite", "obsidian"),
    "White": ("pearl white", "ceramic white", "white", "bialy", "biala",
              "biale", "perlowy", "perlowa", "snow"),
    "Blue": ("glacier blue", "ocean blue", "deep blue", "sky blue", "navy",
             "blue", "niebieski", "niebieska", "niebieskie", "granatowy",
             "granatowa", "lagoon", "ocean", "glacier"),
    "Green": ("forest green", "mint green", "olive green", "green", "zielony",
              "zielona", "zielone", "mietowy", "mietowa", "mint", "olive",
              "forest", "sage"),
    "Purple": ("aurora purple", "lavender", "purple", "violet", "fioletowy",
               "fioletowa", "fioletowe", "lawendowy", "lawendowa", "lilac",
               "aurora"),
    "Pink": ("cloud blush", "blush", "pink", "rozowy", "rozowa", "rozowe",
             "rose", "coral", "koralowy"),
    "Red": ("red", "czerwony", "czerwona", "burgundy", "bordowy", "bordowa"),
    "Orange": ("orange", "pomaranczowy", "pomaranczowa"),
    "Yellow": ("yellow", "zolty", "zolta", "zolte", "lemon"),
    "Gold": ("champagne gold", "gold", "zloty", "zlota", "zlote", "champagne"),
    "Silver": ("silver", "srebrny", "srebrna", "srebrne"),
    "Grey": ("space grey", "space gray", "grey", "gray", "szary", "szara",
             "szare", "stone", "titan gray"),
    "Titanium": ("titanium", "tytanowy", "tytanowa"),
    "Brown": ("brown", "brazowy", "brazowa", "mocha", "coffee"),
    "Beige": ("beige", "sand", "cream", "ivory", "bezowy", "bezowa",
              "kremowy", "kremowa", "piaskowy"),
    "Turquoise": ("turquoise", "teal", "turkusowy", "turkusowa", "cyan"),
}


def detect_colour(title):

    """Wide colour detection; returns 'Unknown' only if nothing matches."""

    text = ascii_text(title)

    pairs = [(w, c) for c, words in COLOUR_WORDS.items() for w in words]

    # longer phrases first: 'cloud blush' before 'blush', 'deep blue' before 'blue'
    for word, colour in sorted(pairs, key=lambda p: -len(p[0])):

        if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text):
            return colour

    return "Unknown"
