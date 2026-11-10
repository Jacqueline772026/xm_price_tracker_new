# Not using for now, the availability detection is complicated and may not be reliable.

import re
import time


# ============================================================
# PRICE
# ============================================================

def clean_price(text):

    if not text:
        return None

    text = str(text).strip()

    text = text.replace("zł", "")
    text = text.replace("PLN", "")
    text = text.replace(" ", "")

    # Keep only numbers / separators
    match = re.search(
        r"\d+[,.]?\d*",
        text
    )

    if not match:
        return None

    value = match.group(0)

    if "," in value:
        value = value.replace(",", ".")

    return float(value)


# ============================================================
# COLOR
# ============================================================

def get_color(text):

    text_lower = text.lower().strip()

    color_map = {

        "black":
            "Black",

        "czarny":
            "Black",

        "czarna":
            "Black",

        "mist blue":
            "Mist Blue",

        "blue":
            "Blue",

        "niebieski":
            "Blue",

        "niebieska":
            "Blue",

        "palm green":
            "Palm Green",

        "green":
            "Green",

        "zielony":
            "Green",

        "zielona":
            "Green",

        "white":
            "White",

        "biały":
            "White",

        "biała":
            "White",

        "titanium":
            "Titanium",

        "tytanowy":
            "Titanium",

        "purple":
            "Purple",

        "fioletowy":
            "Purple",
    }

    for key, value in color_map.items():

        if key in text_lower:
            return value

    return text.strip()


# ============================================================
# NORMALIZE
# ============================================================

def normalize_number(value):

    if value is None:
        return ""

    return re.sub(
        r"\D",
        "",
        str(value)
    )


# ============================================================
# FIND TEXT ELEMENT
# ============================================================

def find_text_element(page, text):

    # Try exact text first
    locator = page.get_by_text(
        text,
        exact=True
    )

    if locator.count() > 0:
        return locator.first

    # Then partial text
    locator = page.get_by_text(
        re.compile(
            re.escape(text),
            re.IGNORECASE
        )
    )

    if locator.count() > 0:
        return locator.first

    return None


# ============================================================
# CLICK OPTION
# ============================================================

def click_option(page, option_text):

    print(
        f"Looking for option: {option_text}"
    )

    element = find_text_element(
        page,
        option_text
    )

    if element is None:

        print(
            f"Option not found: {option_text}"
        )

        return False

    try:

        element.scroll_into_view_if_needed()

    except Exception:
        pass

    # --------------------------------------------------------
    # Check disabled state before clicking
    # --------------------------------------------------------

    try:

        disabled = element.is_disabled()

        if disabled:

            print(
                f"Option disabled: {option_text}"
            )

            return False

    except Exception:
        pass

    # --------------------------------------------------------
    # Inspect DOM state
    # --------------------------------------------------------

    try:

        state = element.evaluate(
            """
            el => ({
                tag: el.tagName,
                className: el.className,
                ariaDisabled: el.getAttribute('aria-disabled'),
                disabled: el.getAttribute('disabled')
            })
            """
        )

        print(
            "OPTION DOM STATE:",
            state
        )

        if (
            state.get("ariaDisabled") == "true"
            or
            state.get("disabled") is not None
        ):

            print(
                f"Option appears disabled: {option_text}"
            )

            return False

    except Exception as e:

        print(
            "Could not inspect option state:",
            str(e)
        )

    # --------------------------------------------------------
    # Click
    # --------------------------------------------------------

    try:

        element.click(
            timeout=3000
        )

    except Exception:

        try:

            element.evaluate(
                "el => el.click()"
            )

        except Exception as e:

            print(
                f"Could not click {option_text}:",
                str(e)
            )

            return False

    time.sleep(0.8)

    return True


# ============================================================
# FIND PRICE
# ============================================================

def extract_price(page):

    # --------------------------------------------------------
    # First look around the main purchase area
    # --------------------------------------------------------

    price_candidates = page.locator(
        "body"
    ).get_by_text(
        re.compile(
            r"\d{2,5}[,.]\d{2}\s*zł",
            re.IGNORECASE
        )
    )

    prices = []

    for i in range(
        min(price_candidates.count(), 30)
    ):

        try:

            text = (
                price_candidates
                .nth(i)
                .inner_text()
                .strip()
            )

            price = clean_price(text)

            if price is not None:
                prices.append(price)

        except Exception:
            continue

    if prices:

        # Usually the first relevant price is the
        # current product price.
        return prices[0]

    # --------------------------------------------------------
    # Fallback: scan body text
    # --------------------------------------------------------

    try:

        body_text = page.locator(
            "body"
        ).inner_text()

        matches = re.findall(
            r"(\d{2,5}[,.]\d{2})\s*zł",
            body_text,
            re.IGNORECASE
        )

        if matches:

            return clean_price(
                matches[0]
            )

    except Exception:
        pass

    return None


# ============================================================
# PURCHASE STATUS
# ============================================================

def get_availability(page):

    try:

        body_text = (
            page.locator(
                "body"
            )
            .inner_text()
            .lower()
        )

    except Exception:

        return "Unknown"

    # --------------------------------------------------------
    # Strongest unavailable signal
    # --------------------------------------------------------

    if (
        "notify me" in body_text
        or
        "powiadom mnie" in body_text
    ):

        return "Unavailable"

    # --------------------------------------------------------
    # Strong available signal
    # --------------------------------------------------------

    if (
        "add to cart" in body_text
        or
        "dodaj do koszyka" in body_text
    ):

        return "Available"

    return "Unknown"


# ============================================================
# GET COLOR OPTIONS
# ============================================================

def get_color_options(page):

    colors = []

    # --------------------------------------------------------
    # Known Redmi A7 Pro colors
    #
    # We also inspect the page text so this remains
    # somewhat flexible.
    # --------------------------------------------------------

    possible_colors = [

        "Black",
        "Mist Blue",
        "Palm Green",

        "Blue",
        "Green",
        "White",
        "Purple",
        "Titanium",

    ]

    for color in possible_colors:

        element = find_text_element(
            page,
            color
        )

        if element is None:
            continue

        # Avoid unrelated occurrences
        try:

            text = (
                element
                .inner_text()
                .strip()
            )

            if color.lower() not in text.lower():
                continue

        except Exception:

            continue

        if color not in colors:

            colors.append(color)

    return colors


# ============================================================
# GET PRODUCTS
# ============================================================

def get_products(page, product):

    results = []

    print(
        "Waiting for Mi.com product page..."
    )

    # --------------------------------------------------------
    # Target RAM / Storage
    # --------------------------------------------------------

    target_ram = normalize_number(
        product["ram"]
    )

    target_storage = normalize_number(
        product["storage"]
    )

    print(
        "Target RAM:",
        target_ram
    )

    print(
        "Target Storage:",
        target_storage
    )

    # --------------------------------------------------------
    # Product title
    # --------------------------------------------------------

    try:

        title = (
            page.locator(
                "h1"
            )
            .first
            .inner_text()
            .strip()
        )

    except Exception:

        title = product["name"]

    print(
        "PAGE TITLE:",
        title
    )

    # --------------------------------------------------------
    # Find RAM/storage option
    #
    # Mi.com uses strings such as:
    #
    # 4GB+64GB
    # 4 GB + 64 GB
    #
    # --------------------------------------------------------

    memory_options = page.locator(
        "text=/4\\s*GB\\s*\\+\\s*64\\s*GB/i"
    )

    print(
        "4+64 memory options:",
        memory_options.count()
    )

    # --------------------------------------------------------
    # Select target memory
    # --------------------------------------------------------

    memory_selected = False

    if memory_options.count() > 0:

        for i in range(
            memory_options.count()
        ):

            option = memory_options.nth(i)

            try:

                text = (
                    option
                    .inner_text()
                    .strip()
                )

            except Exception:

                text = ""

            if (
                normalize_number(text)
                ==
                target_ram + target_storage
            ):

                print(
                    "MEMORY OPTION:",
                    text
                )

                try:

                    option.scroll_into_view_if_needed()

                except Exception:
                    pass

                try:

                    option.click(
                        timeout=3000
                    )

                    memory_selected = True

                    time.sleep(1)

                    break

                except Exception as e:

                    print(
                        "Could not click memory option:",
                        str(e)
                    )

    # --------------------------------------------------------
    # Fallback: exact text search
    # --------------------------------------------------------

    if not memory_selected:

        memory_texts = [

            "4GB+64GB",
            "4 GB + 64 GB",
            "4GB + 64GB",

        ]

        for memory_text in memory_texts:

            element = find_text_element(
                page,
                memory_text
            )

            if element is None:
                continue

            try:

                element.click(
                    timeout=3000
                )

                memory_selected = True

                print(
                    "Selected memory:",
                    memory_text
                )

                time.sleep(1)

                break

            except Exception:
                continue

    if not memory_selected:

        print(
            "WARNING: Could not explicitly select 4+64."
        )

    # --------------------------------------------------------
    # Get colors
    # --------------------------------------------------------

    colors = get_color_options(
        page
    )

    print(
        "Detected colors:",
        colors
    )

    # --------------------------------------------------------
    # If no colors detected, use known colors
    # --------------------------------------------------------

    if not colors:

        colors = [
            "Black",
            "Mist Blue",
            "Palm Green"
        ]

    # --------------------------------------------------------
    # Process each color
    # --------------------------------------------------------

    for color in colors:

        print()
        print(
            "=" * 60
        )
        print(
            "MICOM PRODUCT"
        )
        print(
            "=" * 60
        )

        print(
            "COLOR:",
            color
        )

        # ----------------------------------------------------
        # Reload product page before each variant
        #
        # This prevents one variant selection from affecting
        # another variant.
        # ----------------------------------------------------

        try:

            page.reload(
                wait_until="domcontentloaded"
            )

            time.sleep(1)

        except Exception:
            pass

        # ----------------------------------------------------
        # Select memory again
        # ----------------------------------------------------

        memory_selected = False

        for memory_text in [
            "4GB+64GB",
            "4 GB + 64 GB",
            "4GB + 64GB",
        ]:

            element = find_text_element(
                page,
                memory_text
            )

            if element is None:
                continue

            try:

                element.click(
                    timeout=3000
                )

                memory_selected = True

                time.sleep(0.7)

                break

            except Exception:
                continue

        # ----------------------------------------------------
        # Select color
        # ----------------------------------------------------

        color_element = find_text_element(
            page,
            color
        )

        if color_element is None:

            print(
                "Color not found:",
                color
            )

            continue

        # ----------------------------------------------------
        # Inspect disabled state
        # ----------------------------------------------------

        disabled = False

        try:

            state = color_element.evaluate(
                """
                el => {
                    const parent = el.closest(
                        'button,[role="button"],div'
                    );

                    return {
                        elementClass: el.className,
                        elementAriaDisabled:
                            el.getAttribute('aria-disabled'),
                        elementDisabled:
                            el.getAttribute('disabled'),
                        parentClass:
                            parent ? parent.className : null,
                        parentAriaDisabled:
                            parent
                            ? parent.getAttribute('aria-disabled')
                            : null,
                        parentDisabled:
                            parent
                            ? parent.getAttribute('disabled')
                            : null
                    };
                }
                """
            )

            print(
                "COLOR DOM STATE:",
                state
            )

            if (
                state["elementAriaDisabled"]
                == "true"
                or
                state["parentAriaDisabled"]
                == "true"
                or
                state["elementDisabled"]
                is not None
                or
                state["parentDisabled"]
                is not None
            ):

                disabled = True

        except Exception as e:

            print(
                "Could not inspect color state:",
                str(e)
            )

        # ----------------------------------------------------
        # If explicitly disabled
        # ----------------------------------------------------

        if disabled:

            availability = "Unavailable"

            price = None

            print(
                "COLOR IS DISABLED"
            )

        else:

            # ------------------------------------------------
            # Click color
            # ------------------------------------------------

            try:

                color_element.scroll_into_view_if_needed()

                color_element.click(
                    timeout=3000
                )

                time.sleep(1)

            except Exception as e:

                print(
                    "Could not select color:",
                    str(e)
                )

            # ------------------------------------------------
            # Read purchase state
            # ------------------------------------------------

            availability = get_availability(
                page
            )

            # ------------------------------------------------
            # Read price
            # ------------------------------------------------

            price = extract_price(
                page
            )

        print(
            "PRICE:",
            price
        )

        print(
            "AVAILABILITY:",
            availability
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        results.append({

            "product_name":
                product["name"],

            "variant":
                get_color(color),

            "ram":
                product["ram"] + " GB",

            "storage":
                product["storage"] + " GB",

            "price":
                price,

            "availability":
                availability,

        })

    return results


# ============================================================
# UNIFIED SCRAPER INTERFACE
# ============================================================

def get_price(page, product=None):

    if product is None:
        return None

    return get_products(
        page,
        product
    )