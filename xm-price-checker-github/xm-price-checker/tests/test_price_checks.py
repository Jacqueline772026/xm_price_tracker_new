import os
import sys
import unittest
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import price_checks as pc  # noqa: E402

PRODUCTS = {
    "LEEDSA-4-128": {"name": "Redmi 17", "ram": "4", "storage": "128"},
    "MOSCOW-8-512": {"name": "Redmi Note 17 Pro 5G", "ram": "8", "storage": "512"},
    "P12U-12-1T": {"name": "Xiaomi 17T Pro 5G", "ram": "12", "storage": "1T"},
    "O84E-4-128": {"name": "Redmi Pad 2", "ram": "4", "storage": "128"},
}

NOW = datetime(2026, 11, 7, 9, 0)


def row(target, site, colour, price, avail="Available", status="OK", error=""):
    return {"run_time": NOW, "target_id": target, "website": site,
            "variant": colour, "price": price, "availability": avail,
            "status": status, "error": error}


def checks(findings):
    return {(f["check"], f["site"], f["target"]) for f in findings}


class LinkChecks(unittest.TestCase):

    def link(self, target, site, query):
        return {"target_id": target, "website": site,
                "url": f"https://x.pl/search?query[querystring]={query}"}

    def test_wrong_memory_in_link_is_high(self):
        f = pc.check_links(
            [self.link("MOSCOW-8-512", "Electro.pl",
                       "Redmi%20Note%2017%20Pro%205G%206256")], PRODUCTS)
        self.assertEqual(f[0]["severity"], "HIGH")
        self.assertEqual(f[0]["check"], "link-memory")

    def test_correct_link_formats_pass(self):
        good = [
            ("MOSCOW-8-512", "Redmi%20Note%2017%20Pro%205G%208%2F512"),
            ("MOSCOW-8-512", "Redmi%20Note%2017%20Pro%205G%208512"),
            ("MOSCOW-8-512", "Redmi+Note+17+Pro+5G+8/512"),
            ("P12U-12-1T", "Xiaomi%2017T%20PRO%205G%201TB"),
            ("P12U-12-1T", "Xiaomi%2017T%20PRO%205G%2012%2F1TB"),
            ("LEEDSA-4-128", "Redmi%2017%204%2F128"),
        ]
        for target, query in good:
            with self.subTest(query=query):
                f = pc.check_links([self.link(target, "MEX", query)], PRODUCTS)
                self.assertEqual([x for x in f if x["severity"] != "LOW"], [])

    def test_rm_in_search_words_means_redmi(self):
        f = pc.check_links([self.link("MOSCOW-8-512", "MSH",
                                      "rm+note+17+pro+5g+8/512")], PRODUCTS)
        self.assertNotIn("link-name", [x["check"] for x in f])

    def test_unknown_target(self):
        f = pc.check_links([self.link("NOPE-1-1", "MEX", "abc")], PRODUCTS)
        self.assertEqual(f[0]["check"], "link-target")


class ResultChecks(unittest.TestCase):

    LINKS = [{"target_id": "LEEDSA-4-128", "website": s, "url": "u"}
             for s in ("MEX", "MSH", "XKOM", "KTR")]

    def test_site_returning_nothing_is_high(self):
        rows = [row("LEEDSA-4-128", s, "Black", 799) for s in ("MEX", "XKOM", "KTR")]
        f = pc.check_results(rows, self.LINKS)
        self.assertIn(("site-empty", "MSH", "*"), checks(f))

    def test_scraper_error_is_high(self):
        rows = [row("LEEDSA-4-128", "MSH", "", None, "Unknown", "ERROR", "boom")]
        f = pc.check_results(rows, self.LINKS)
        self.assertIn(("scraper-error", "MSH", "LEEDSA-4-128"), checks(f))

    def test_same_colour_two_prices(self):
        rows = [row("LEEDSA-4-128", "MEX", "Black", 799),
                row("LEEDSA-4-128", "MEX", "Black", 949)]
        f = pc.check_results(rows, self.LINKS)
        self.assertIn(("same-colour-prices", "MEX", "LEEDSA-4-128"), checks(f))
        self.assertEqual([x["severity"] for x in f if x["check"] == "same-colour-prices"], ["LOW"])

    def test_layout_changed_alarm(self):
        rows = [row("LEEDSA-4-128", "KTR", "Black", 799, "Unknown") for _ in range(4)]
        rows += [row("LEEDSA-4-128", s, "Black", 799) for s in ("MEX", "XKOM", "MSH")]
        f = pc.check_results(rows, self.LINKS)
        self.assertIn(("layout-changed", "KTR", "*"), checks(f))
        self.assertNotIn(("layout-changed", "MEX", "*"), checks(f))

    def test_rrp_is_ignored_only_promo_counts(self):
        # price above RRP (899) but close to the promo price -> no finding
        rows = [row("LEEDSA-4-128", s, "Black", 949) for s in ("MEX", "XKOM", "KTR")]
        promo = {"LEEDSA-4-128": {"rrp": 899, "promo": 949}}
        f = pc.check_results(rows, self.LINKS, promo)
        self.assertNotIn("far-above-promo", [x["check"] for x in f])
        self.assertNotIn("above-rrp", [x["check"] for x in f])

    def test_same_colour_prices_is_low_and_ignores_decimals(self):
        rows = [row("LEEDSA-4-128", "MEX", "Blue", 2799),
                row("LEEDSA-4-128", "MEX", "Blue", 2799.99)]
        f = pc.check_results(rows, self.LINKS)
        self.assertNotIn(("same-colour-prices", "MEX", "LEEDSA-4-128"), checks(f))

    def test_above_rrp_and_outlier(self):
        rows = [row("LEEDSA-4-128", s, "Black", 799) for s in ("MEX", "XKOM", "KTR")]
        rows.append(row("LEEDSA-4-128", "MSH", "Green", 1100))
        promo = {"LEEDSA-4-128": {"rrp": 899, "promo": 799}}
        f = pc.check_results(rows, self.LINKS, promo)
        c = checks(f)
        self.assertIn(("far-above-promo", "MSH", "LEEDSA-4-128"), c)
        self.assertIn(("price-outlier", "MSH", "LEEDSA-4-128"), c)

    def test_price_at_promo_is_not_an_outlier(self):
        rows = [row("LEEDSA-4-128", "MEX", "Black", 700),
                row("LEEDSA-4-128", "XKOM", "Black", 700),
                row("LEEDSA-4-128", "KTR", "Black", 700),
                row("LEEDSA-4-128", "MSH", "Black", 799)]
        promo = {"LEEDSA-4-128": {"rrp": 899, "promo": 799}}
        f = pc.check_results(rows, self.LINKS, promo)
        self.assertNotIn(("price-outlier", "MSH", "LEEDSA-4-128"), checks(f))

    def test_unknown_availability_and_missing_price(self):
        rows = [row("LEEDSA-4-128", "KTR", "Black", 799, "Unknown"),
                row("LEEDSA-4-128", "MEX", "Black", None, "Available")]
        c = checks(pc.check_results(rows, self.LINKS))
        self.assertIn(("availability-unknown", "KTR", "LEEDSA-4-128"), c)
        self.assertIn(("no-price", "MEX", "LEEDSA-4-128"), c)

    def test_only_latest_day_is_checked(self):
        old = row("LEEDSA-4-128", "MEX", "Black", None, "Unknown")
        old["run_time"] = datetime(2026, 10, 1, 9, 0)
        new = row("LEEDSA-4-128", "MEX", "Black", 799)
        f = pc.check_results([old, new], self.LINKS)
        self.assertNotIn(("availability-unknown", "MEX", "LEEDSA-4-128"), checks(f))


class InputChecks(unittest.TestCase):

    def test_promo_above_rrp_is_not_flagged(self):
        # the user's typed prices are authoritative
        self.assertEqual(
            pc.check_promo_inputs({"P10-12-512": {"rrp": 1899, "promo": 1999}}), [])

    def test_clean_input(self):
        self.assertEqual(
            pc.check_promo_inputs({"A": {"rrp": 899, "promo": 799}}), [])


class Report(unittest.TestCase):

    def test_report_text(self):
        self.assertIn("Nothing suspicious", pc.format_report([]))
        f = pc.run_checks([], [], {}, {"P": {"rrp": 1, "promo": None}})
        self.assertIn("MEDIUM: 1", pc.format_report(f))


if __name__ == "__main__":
    unittest.main(verbosity=2)


class StaleRows(unittest.TestCase):

    def test_rows_before_promo_start_are_dropped(self):
        import datetime as dt
        import price_checks as pc
        rows = [{"run_time": dt.datetime(2026, 10, 20, 9)},
                {"run_time": dt.datetime(2026, 11, 10, 9)}]
        kept, n = pc.drop_stale_rows(rows, dt.date(2026, 11, 9))
        self.assertEqual((len(kept), n), (1, 1))

    def test_no_start_date_keeps_everything(self):
        import price_checks as pc
        rows = [{"run_time": None}]
        self.assertEqual(pc.drop_stale_rows(rows, None), (rows, 0))
