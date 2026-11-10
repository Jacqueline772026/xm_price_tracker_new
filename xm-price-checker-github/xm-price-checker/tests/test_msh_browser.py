"""
Browser-level test for scrapers/msh.py.

It loads small local HTML pages that copy the DOM structure of the real
MediaMarkt result cards (data-test attributes, strike-price block,
instalment text, marketplace seller link) into a real browser and runs the
real msh.get_products() on them. No network is used.

Skipped automatically when Playwright or a browser is not available.
Set CHROME_PATH to use a specific Chrome/Chromium executable.
"""

import contextlib
import io
import os
import shutil
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None

from scrapers import msh  # noqa: E402


def official_html(title, price, delivery="AVAILABLE", refurb=False):
    avail = (
        "Dostępny online" if delivery == "AVAILABLE"
        else "Niestety dostawa nie jest możliwa"
    )
    refurb_html = (
        "<div>Dostępne są oferty produktów odnowionych od 639,– zł</div>"
        if refurb else ""
    )
    basket = (
        '<button data-test="cofr-add-to-basket-button a2c-Button">Dodaj do koszyka</button>'
        if delivery == "AVAILABLE" else ""
    )
    return f"""
<article data-test="mms-cofr-product-card">
  <div data-test="cofr-card-product-badges">Raty 0%</div>
  <a href="#">Karta produktu</a>
  <a data-test="product-list-item-link" href="#">{title}</a>
  <div data-test="mms-cofr-delivery_{delivery}">{avail}</div>
  <div data-test="mms-cofr-pickup_NO_STORE_SELECTED">Sprawdź odbiór w sklepie</div>
  {refurb_html}
  <div data-test="cofr-price mms-price">
    <div></div>
    <div><span aria-hidden="true">{price},–&nbsp;zł</span><span>{price},00zł</span></div>
    <div><div>
      <div data-test="additional-info-normal-wrapper"><p data-test="additional-info-normal">
        <button type="button"><span><span>zawiera podatek VAT, darmowa dostawa</span></span></button></p></div>
      <div data-test="additional-info-normal-wrapper"><p data-test="additional-info-normal">
        <strong>Rozłóż na raty.</strong> Płać już od 26,08&nbsp;zł miesięcznie</p></div>
    </div></div>
  </div>
  {basket}
</article>"""


def market_html(title, price, reference=None):
    strike = (
        f"""<div><div><div><span>-25%</span></div></div>
        <div data-test="mms-strike-price-type-lop"><span data-test="mms-strike-price-label">Najniższa cena:</span>
        <span aria-hidden="true">{reference},–&nbsp;zł</span><span>{reference},00zł</span></div>
        <button type="button" aria-label="Najniższa cena z 30 dni przed obniżką">i</button></div>"""
        if reference else ""
    )
    return f"""
<article data-test="mms-cofr-product-card">
  <a href="#">{title}</a>
  <div data-test="mms-cofr-delivery_PARTIALLY_AVAILABLE">Złóż zamówienie dzisiaj</div>
  <div data-test="cofr-price mms-price">
    {strike}
    <div><span aria-hidden="true">{price},–&nbsp;zł</span><span>{price},00zł</span></div>
    <div><div><div data-test="additional-info-normal-wrapper"><p data-test="additional-info-normal">
      <a data-test="mms-router-link" href="https://mediamarkt.pl/pl/marketplace/seller/13350">
        <span>zawiera podatek VAT, darmowa dostawa</span></a></p></div>
      <div data-test="additional-info-normal-wrapper"><p data-test="additional-info-normal">
        Sprzedaż i wysyłka przez <a data-test="mms-third-party-provider-link"
        href="https://mediamarkt.pl/pl/marketplace/seller/13350"><span>TecnoFlow PL</span></a></p></div>
    </div></div>
  </div>
</article>"""


def page_html(*cards, header="Wynik wyszukiwania dla: x (21)"):
    return f"<html><body><h1>{header}</h1>{''.join(cards)}</body></html>"


def find_chrome():
    env = os.environ.get("CHROME_PATH")
    if env:
        return env
    for name in ("google-chrome", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    return None


@unittest.skipIf(sync_playwright is None, "playwright not installed")
class BrowserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        exe = find_chrome()
        try:
            kwargs = {"headless": True}
            if exe:
                kwargs["executable_path"] = exe
            cls.browser = cls.pw.chromium.launch(**kwargs)
        except Exception as e:  # pragma: no cover
            cls.pw.stop()
            raise unittest.SkipTest(f"no browser available: {e}")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def run_msh(self, html, name, ram, storage):
        page = self.browser.new_page()
        try:
            page.set_content(html)
            with contextlib.redirect_stdout(io.StringIO()):
                return msh.get_products(
                    page,
                    {"name": name, "ram": str(ram), "storage": str(storage)},
                )
        finally:
            page.close()

    def test_real_dom_structure_official_only_current_price(self):
        html = page_html(
            official_html("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Niebieski", 3799),
            market_html("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Purple", 3739, reference=4999),
            official_html("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Czarny", 3799, refurb=True),
            official_html("Smartfon XIAOMI 17T Pro 5G 12 GB/ 1 TB Fioletowy", 4499,
                          delivery="NOT_AVAILABLE"),
            official_html("Smartfon XIAOMI 17T Pro 5G 12 GB/ 512 GB Czarny", 3499),
        )
        res = self.run_msh(html, "Xiaomi 17T Pro 5G", 12, "1T")
        got = sorted((r["variant"], r["price"], r["availability"]) for r in res)
        self.assertEqual(
            got,
            [("Black", 3799.0, "Available"),
             ("Blue", 3799.0, "Available"),
             ("Purple", 4499.0, "Unavailable")],
        )

    def test_old_selector_would_have_found_nothing(self):
        html = page_html(
            official_html("Smartfon XIAOMI REDMI 17 4G (LTE) 4 GB/ 128 GB Zielony", 799))
        page = self.browser.new_page()
        page.set_content(html)
        old = page.locator('article[data-test="mms-product-card"]').count()
        new = page.locator(msh.CARD_SELECTOR).count()
        page.close()
        self.assertEqual((old, new), (0, 1))

    def test_blank_page_is_an_error_not_silent_empty(self):
        with self.assertRaises(RuntimeError):
            self.run_msh("<html><body><h1>Hello</h1></body></html>",
                         "Redmi 17", 4, 128)

    def test_blocked_page_stops(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.run_msh("<html><body>Just a moment... verify you are human</body></html>",
                         "Redmi 17", 4, 128)
        self.assertIn("anti-bot", str(ctx.exception))

    def test_zero_results_is_unavailable_row(self):
        res = self.run_msh(
            "<html><body><h1>Wynik wyszukiwania dla: abc (0)</h1></body></html>",
            "Redmi 17", 4, 128)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["availability"], "Unavailable")
        self.assertIsNone(res[0]["price"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
