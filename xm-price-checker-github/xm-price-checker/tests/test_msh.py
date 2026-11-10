"""
Offline tests for the MediaMarkt (MSH) scraper and the shared matching helpers.

Run from the project root:
    python -m unittest discover -s tests -v

The card dictionaries below have exactly the shape CARD_JS returns, and were
modelled on real MediaMarkt result cards seen on 2026-11-07 (official card,
official unavailable card, marketplace card with a crossed-out "Najniższa
cena" reference price).
"""

import contextlib
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scrapers import matching, msh  # noqa: E402


def quiet(fn, *args, **kwargs):
    """Call fn with its (very chatty) prints suppressed."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


# ------------------------------------------------------------
# Card builders (same shape as CARD_JS output)
# ------------------------------------------------------------

def official(title, price, delivery="AVAILABLE", extra_text=""):
    whole = f"{price},– zł"
    exact = f"{price},00zł"
    avail = (
        "Dostępny online\nZłóż zamówienie dzisiaj, a my dostarczymy je od 09.11.2026"
        if delivery == "AVAILABLE"
        else "Niestety dostawa nie jest możliwa"
    )
    text = (
        f"Karta produktu\n{title}\n{avail}\nSprawdź odbiór w sklepie\n"
        f"{extra_text}{whole}\n{exact}\n\nzawiera podatek VAT, darmowa dostawa\n\n"
        "Rozłóż na raty. Płać już od 26,08 zł miesięcznie (więcej w opisie produktu)\n"
        "Dodaj do porównania\nDodaj do koszyka"
    )
    return {
        "title": title,
        "links": ["Karta produktu", title],
        "hasPriceBox": True,
        "priceTexts": [whole, exact],
        "thirdParty": False,
        "delivery": delivery,
        "text": text,
    }


def marketplace(title, price, reference=None, seller="TecnoFlow PL"):
    whole = f"{price},– zł"
    exact = f"{price},00zł"
    ref_text = (
        f"-25%\nNajniższa cena: {reference},– zł\n{reference},00zł\n"
        if reference else ""
    )
    price_texts = (["-25%"] if reference else []) + [whole, exact]
    text = (
        f"{title}\nZłóż zamówienie dzisiaj, a dostarczymy je w dniach 16.11.2026 - 19.11.2026\n"
        f"{ref_text}{whole}\n{exact}\n\nzawiera podatek VAT, darmowa dostawa\n\n"
        f"Sprzedaż i wysyłka przez {seller}\n\nDodaj do koszyka"
    )
    return {
        "title": "",
        "links": [title, "zawiera podatek VAT, darmowa dostawa", seller],
        "hasPriceBox": True,
        "priceTexts": price_texts,
        "thirdParty": True,
        "delivery": "PARTIALLY_AVAILABLE",
        "text": text,
    }


def unproven(title, price):
    """Card with no seller line and no self-pickup block (still official)."""
    card = marketplace(title, price)
    card["thirdParty"] = False
    card["text"] = card["text"].replace(
        "Sprzedaż i wysyłka przez TecnoFlow PL\n\n", ""
    )
    return card


def product(name, ram, storage):
    return {"name": name, "ram": str(ram), "storage": str(storage),
            "target_id": "x", "model": "x"}


# Page modelled on the real "Xiaomi 17T PRO 5G 1TB" search
PAGE_17T = [
    official("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Niebieski", 3799),
    marketplace("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Czarny", 3739),
    official("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Czarny", 3799,
             extra_text="Dostępne są oferty produktów odnowionych od 3199,– zł\n"),
    marketplace("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Purple", 3739, reference=4999),
    marketplace("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Blue", 3739, reference=4999),
    official("Smartfon XIAOMI 17T Pro 5G 12 GB/ 512 GB Fioletowy", 3499),
    official("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Fioletowy", 4499,
             delivery="NOT_AVAILABLE"),
    official("Smartfon XIAOMI 17T Pro 5G 12 GB/ 512 GB Niebieski", 3499),
    official("Smartfon XIAOMI 17T Pro 5G 12 GB/ 512 GB Czarny", 3499),
    marketplace("Smartfon XIAOMI 17T Pro 5G 12 GB/ 512 GB Black", 3259, reference=4299),
]

# Page modelled on the real "Redmi 17 4/128" search
PAGE_REDMI17 = [
    official("Smartfon XIAOMI REDMI 17 4G (LTE) 4 GB/ 128 GB Niebieski", 899),
    official("Smartfon XIAOMI REDMI 17 4G (LTE) 4 GB/ 128 GB Zielony", 799),
    official("Smartfon XIAOMI REDMI 17 4G (LTE) 4 GB/ 128 GB Czarny", 899,
             extra_text="Dostępne są oferty produktów odnowionych od 639,– zł\n"),
    marketplace("Smartfon XIAOMI Redmi Note 17 4G (LTE) 4 GB/ 128 GB Fioletowy", 919),
    marketplace("Smartfon XIAOMI Redmi 17 5G 4 GB/ 128 GB Czarny", 919),
    marketplace("Smartfon XIAOMI REDMI 17 4G (LTE) 4 GB/ 128 GB Fioletowy", 915,
                seller="Electronic Shops PL"),
]


def rows(result):
    return sorted(
        (r["variant"], r["price"], r["availability"]) for r in result
    )


class SellerAndPrice(unittest.TestCase):

    def test_official_only_and_correct_prices_1tb(self):
        res = quiet(msh.build_results, PAGE_17T,
                    product("Xiaomi 17T Pro 5G", 12, "1T"))
        self.assertEqual(
            rows(res),
            [("Black", 3799.0, "Available"),
             ("Blue", 3799.0, "Available"),
             ("Purple", 4499.0, "Unavailable")],
        )

    def test_marketplace_reference_price_never_used(self):
        res = quiet(msh.build_results, PAGE_17T,
                    product("Xiaomi 17T Pro 5G", 12, "1T"))
        self.assertNotIn(4999.0, [r["price"] for r in res])
        self.assertNotIn(3739.0, [r["price"] for r in res])

    def test_512_variant(self):
        res = quiet(msh.build_results, PAGE_17T,
                    product("Xiaomi 17T Pro 5G", 12, "512"))
        self.assertEqual(
            rows(res),
            [("Black", 3499.0, "Available"),
             ("Blue", 3499.0, "Available"),
             ("Purple", 3499.0, "Available")],
        )

    def test_refurbished_teaser_is_not_the_price(self):
        res = quiet(msh.build_results, PAGE_REDMI17, product("Redmi 17", 4, 128))
        black = [r for r in res if r["variant"] == "Black"][0]
        self.assertEqual(black["price"], 899.0)

    def test_redmi17_does_not_pick_note17_or_5g_or_marketplace(self):
        res = quiet(msh.build_results, PAGE_REDMI17, product("Redmi 17", 4, 128))
        self.assertEqual(
            rows(res),
            [("Black", 899.0, "Available"),
             ("Blue", 899.0, "Available"),
             ("Green", 799.0, "Available")],
        )

    def test_official_discounted_card_uses_current_price(self):
        card = official("Smartfon XIAOMI REDMI 17 4G (LTE) 4 GB/ 128 GB Czarny", 799)
        card["priceTexts"] = ["-25%", "799,– zł", "799,00zł"]
        card["text"] = card["text"].replace(
            "799,– zł", "-25%\nNajniższa cena: 1099,– zł\n1099,00zł\n799,– zł", 1)
        res = quiet(msh.build_results, [card], product("Redmi 17", 4, 128))
        self.assertEqual(res[0]["price"], 799.0)

    def test_price_fallback_from_text_skips_reference_and_instalment(self):
        text = (
            "Smartfon\n-25%\nNajniższa cena: 4999,– zł\n4999,00zł\n"
            "3739,– zł\n3739,00zł\nRozłóż na raty. Płać już od 110,18 zł miesięcznie"
        )
        self.assertEqual(matching.price_from_card_text(text), 3739.0)


class NameMatching(unittest.TestCase):

    def test_redmi_note_17_is_not_redmi_17_even_if_official(self):
        # The old code accepted this (words in order, anything between).
        card = official("Smartfon XIAOMI Redmi Note 17 4G (LTE) 4 GB/ 128 GB Czarny", 1099)
        res = quiet(msh.build_results, [card], product("Redmi 17", 4, 128))
        self.assertEqual(len(res), 1)
        self.assertIsNone(res[0]["price"])
        self.assertEqual(res[0]["availability"], "Unavailable")

    def test_pairs(self):
        cases = [
            ("Redmi Pad 2", "Tablet XIAOMI Redmi Pad 2 11 4 GB/ 128 GB Szary", True),
            ("Redmi Pad 2", "Tablet XIAOMI Redmi Pad 2 Pro 12.1 5G 6GB 128GB", False),
            ("Redmi Pad 2 Pro", "Tablet XIAOMI Redmi Pad 2 Pro 12 1 6 GB/ 128 GB", True),
            ("Redmi Pad 2 Pro 5G", "Tablet XIAOMI Redmi Pad 2 Pro 5G 6 GB/ 128 GB", True),
            ("Xiaomi 17", "Smartfon XIAOMI 17 12 GB/ 512 GB Czarny", True),
            ("Xiaomi 17", "Smartfon XIAOMI 17 Ultra 16 GB/ 512 GB Czarny", False),
            ("Xiaomi 17", "Smartfon XIAOMI 17T 12 GB/ 512 GB Czarny", False),
            ("Xiaomi 17T 5G", "Smartfon XIAOMI 17T Pro 5G 12 GB/ 512 GB", False),
            ("Xiaomi 17T Pro 5G", "Smartfon XIAOMI 17T Pro 5G 12 GB/ 512 GB", True),
            ("POCO X8 Pro", "Smartfon POCO X8 Pro 5G 12 GB/ 512 GB Czarny", True),
            ("POCO X8 Pro", "Smartfon POCO X8 Pro Max 5G 12 GB/ 512 GB", False),
            ("POCO X8", "Smartfon POCO X8 Pro 5G 8 GB/ 256 GB", False),
            ("Redmi 17", "Smartfon XIAOMI Redmi Note 17 4G 4 GB/ 128 GB", False),
            ("Redmi Note 17", "Smartfon XIAOMI Redmi Note 17 4G (LTE) 4 GB/ 128 GB", True),
        ]
        for target, title, expected in cases:
            with self.subTest(target=target, title=title):
                got = quiet(msh.matches_product, title, {"name": target})
                self.assertEqual(got, expected)


class LooseButCorrect(unittest.TestCase):
    """RM = Redmi; a missing 5G is fine; real conflicts are still rejected."""

    def m(self, target, title, sibling=False):
        return quiet(msh.matches_product, title,
                     {"name": target, "has_5g_sibling": sibling})

    def test_rm_means_redmi(self):
        self.assertTrue(self.m("Redmi Note 17", "Smartfon XIAOMI RM Note 17 4G 8 GB/ 256 GB"))
        self.assertTrue(self.m("Redmi 17", "Smartfon RM 17 4 GB/ 128 GB"))
        self.assertFalse(self.m("Redmi 17", "Smartfon RM Note 17 4 GB/ 128 GB"))

    def test_missing_5g_in_title_is_fine_for_5g_only_phones(self):
        self.assertTrue(self.m("Xiaomi 17T Pro 5G", "Smartfon XIAOMI 17T Pro 12 GB/ 512 GB"))
        self.assertTrue(self.m("POCO M8 5G", "Smartfon POCO M8 8 GB/ 256 GB"))

    def test_5g_in_title_but_not_in_name_is_fine_without_a_4g_version(self):
        self.assertTrue(self.m("POCO M8 Pro", "Smartfon POCO M8 Pro 5G 12 GB/ 512 GB"))

    def test_explicit_contradiction_is_rejected(self):
        self.assertFalse(self.m("Redmi Note 17 5G", "Smartfon XIAOMI Redmi Note 17 4G (LTE) 8 GB/ 256 GB"))

    def test_pair_of_4g_and_5g_products_stays_strict(self):
        # Products sheet has both "Redmi Note 17" and "Redmi Note 17 5G"
        self.assertFalse(self.m("Redmi Note 17", "Smartfon XIAOMI Redmi Note 17 5G 8 GB/ 256 GB", True))
        self.assertTrue(self.m("Redmi Note 17", "Smartfon XIAOMI Redmi Note 17 4G (LTE) 8 GB/ 256 GB", True))
        self.assertTrue(self.m("Redmi Note 17 5G", "Smartfon XIAOMI Redmi Note 17 5G 8 GB/ 256 GB", True))
        self.assertFalse(self.m("Redmi Note 17 5G", "Smartfon XIAOMI Redmi Note 17 8 GB/ 256 GB", True))

    def test_loose_does_not_confuse_models(self):
        self.assertFalse(self.m("Xiaomi 17T Pro 5G", "Smartfon XIAOMI 17T 12 GB/ 512 GB"))
        self.assertFalse(self.m("POCO M8 5G", "Smartfon POCO M8 Pro 12 GB/ 512 GB"))


class SellerClassification(unittest.TestCase):

    def test_marketplace_line(self):
        v, _ = matching.classify_seller("x\nSprzedaż i wysyłka przez Deluxury\n", False)
        self.assertEqual(v, "marketplace")

    def test_marketplace_link_without_text(self):
        v, _ = matching.classify_seller("x", True)
        self.assertEqual(v, "marketplace")

    def test_no_seller_line_is_official(self):
        # original rule: no "Sprzedaż i wysyłka przez XX" = official offer
        self.assertEqual(matching.classify_seller("x", False)[0], "official")

    def test_card_without_seller_line_is_used(self):
        card = unproven("Smartfon XIAOMI REDMI 17 4G (LTE) 4 GB/ 128 GB Czarny", 899)
        res = quiet(msh.build_results, [card], product("Redmi 17", 4, 128))
        self.assertEqual(rows(res), [("Black", 899.0, "Available")])


class Parsing(unittest.TestCase):

    def test_prices(self):
        for text, expected in [
            ("3739,– zł", 3739.0), ("3739,00zł", 3739.0),
            ("1 299,00 zł", 1299.0), ("1.299,99 zł", 1299.99),
            ("1065,87 zł", 1065.87), ("2\xa0399,– zł", 2399.0),
        ]:
            with self.subTest(text=text):
                self.assertEqual(matching.parse_price_text(text), expected)
        for bad in ["-25%", "Najniższa cena: 4999,– zł",
                    "Płać już od 26,08 zł miesięcznie", "", None]:
            with self.subTest(bad=bad):
                self.assertIsNone(matching.parse_price_text(bad))

    def test_availability(self):
        f = matching.availability_from_card
        self.assertEqual(f("AVAILABLE", ""), "Available")
        self.assertEqual(f("NOT_AVAILABLE", ""), "Unavailable")
        self.assertEqual(f("", "Niestety dostawa nie jest możliwa"), "Unavailable")
        self.assertEqual(f("", "Dostępny online"), "Available")
        self.assertEqual(f("", "???"), "Unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
