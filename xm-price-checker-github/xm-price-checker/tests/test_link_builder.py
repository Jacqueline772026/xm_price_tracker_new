import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import link_builder as lb  # noqa: E402
import price_checks as pc  # noqa: E402

A7 = {"name": "Redmi A7 pro", "ram": "4", "storage": "64"}
X17T = {"name": "Xiaomi 17T Pro 5G", "ram": "12", "storage": "1T"}
M512 = {"name": "Redmi Note 17 Pro 5G", "ram": "8", "storage": "512"}

PRODUCTS = {"SOMALIAA-4-64": A7, "P12U-12-1T": X17T, "MOSCOW-8-512": M512}


class Build(unittest.TestCase):

    def check(self, site, product, expected, target=None):
        got = lb.build_url(site, product, target, overrides={})
        self.assertEqual(got.lower(), expected.lower())

    def test_each_site_matches_the_links_used_today(self):
        self.check("MEX", A7,
                   "https://www.mediaexpert.pl/search?query[menu_item]=&query[querystring]=Redmi%20A7%20pro%204%2F64")
        self.check("Electro.pl", A7,
                   "https://www.electro.pl/search?query[menu_item]=&query[querystring]=Redmi%20A7%20pro%20464")
        self.check("Avans", A7,
                   "https://www.avans.pl/search?query[menu_item]=&query[querystring]=Redmi%20A7%20pro%20464")
        self.check("MSH", A7,
                   "https://mediamarkt.pl/pl/search.html?query=Redmi%20A7%20pro%204%2F64")
        self.check("KTR", A7,
                   "https://www.komputronik.pl/search/category/1?query=Redmi+A7+pro+4/64")
        self.check("XKOM", A7,
                   "https://www.x-kom.pl/szukaj?q=Redmi%20A7%20pro%204%2F64")
        self.check("NEONET", A7,
                   "https://www.neonet.pl/szukaj?q=Redmi%20A7%20pro%204%2F64")
        self.check("Max electro", A7,
                   "https://maxelektro.pl/wyniki-wyszukiwania?query=Redmi%20A7%20pro%204/64")

    def test_1tb_has_no_ram(self):
        self.check("MSH", X17T,
                   "https://mediamarkt.pl/pl/search.html?query=Xiaomi%2017T%20Pro%205G%201TB")

    def test_memory_is_always_the_products_memory(self):
        for site in lb.SITE_RULES:
            text = lb.search_text(site, M512, "MOSCOW-8-512", overrides={})
            self.assertTrue(text.endswith("8/512") or text.endswith("8512"), text)

    def test_override_wins(self):
        text = lb.search_text("Avans", A7, "SOMALIAA-4-64",
                              overrides={"AVANS": {"SOMALIAA-4-64": "redmi a7"}})
        self.assertEqual(text, "redmi a7")


class Compare(unittest.TestCase):

    def link(self, target, site, text):
        rule = lb.SITE_RULES[lb.site_key(site)]
        return {"target_id": target, "website": site,
                "url": rule["prefix"] + lb.encode(site, text), "enabled": "yes"}

    def test_the_three_old_typos_are_caught(self):
        wrong = [self.link("MOSCOW-8-512", "Electro.pl", "Redmi Note 17 Pro 5G 6256"),
                 self.link("MOSCOW-8-512", "Avans", "Redmi Note 17 Pro 5G 6256")]
        _, differing, _, _ = lb.compare(PRODUCTS, wrong, overrides={})
        self.assertEqual(len(differing), 2)

    def test_correct_links_are_identical(self):
        good = [self.link("MOSCOW-8-512", "Electro.pl", "Redmi Note 17 Pro 5G 8512"),
                self.link("MOSCOW-8-512", "MSH", "Redmi Note 17 Pro 5G 8/512")]
        matching, differing, _, _ = lb.compare(PRODUCTS, good, overrides={})
        self.assertEqual((len(matching), len(differing)), (2, 0))

    def test_price_checks_flags_a_link_that_differs(self):
        wrong = [self.link("MOSCOW-8-512", "KTR", "Redmi Note 17 Pro 5G 8/256")]
        f = pc.check_links_generated(wrong, PRODUCTS)
        self.assertEqual(f[0]["check"], "link-differs")

    def test_overrides_file_keeps_todays_hand_tuned_links(self):
        over = lb.load_overrides()
        self.assertIn("AVANS", over)
        self.assertGreaterEqual(sum(len(v) for v in over.values()), 30)


class NewRows(unittest.TestCase):

    def test_rows_for_a_new_product(self):
        rows = lb.new_rows(PRODUCTS, "moscow-8-512", ["MEX", "Electro.pl"], overrides={})
        self.assertEqual([r[1] for r in rows], ["MEX", "Electro.pl"])
        self.assertTrue(rows[0][2].endswith("8%2F512"))
        self.assertTrue(rows[1][2].endswith("8512"))
        self.assertEqual(rows[0][3], "yes")

    def test_unknown_product(self):
        with self.assertRaises(KeyError):
            lb.new_rows(PRODUCTS, "NOPE-1-1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
