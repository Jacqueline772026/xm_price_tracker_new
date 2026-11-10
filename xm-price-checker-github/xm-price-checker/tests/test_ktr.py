import unittest

from scrapers import ktr, matching


class Availability(unittest.TestCase):

    def test_real_card_phrases(self):
        c = matching.classify_availability
        self.assertEqual(c("2 399 zł Wysyłamy najczęściej w 1 dzień roboczy "
                           "Produkt dostepny w magazynie głównym"), "Available")
        self.assertEqual(c("899 zł Wysyłka najczęściej w 1 dzień roboczy "
                           "Produkt wysyłamy z salonu Dostępny w salonach"), "Available")
        self.assertEqual(c("3 599 zł Czekamy na dostawę towaru Zamówienie "
                           "zostanie przekazane do wysyłki"), "Unavailable")

    def test_unavailable_wins_over_dostepny(self):
        self.assertEqual(
            matching.classify_availability(
                "Produkt tymczasowo niedostępny. Powiadom o dostępności"),
            "Unavailable")

    def test_unknown_only_when_no_signal(self):
        self.assertEqual(matching.classify_availability("Xiaomi 3 599 zł"), "Unknown")


class Other(unittest.TestCase):

    def test_other_shop_wordings(self):
        c = matching.classify_availability
        self.assertEqual(c("Produkt tymczasowo niedostępny"), "Unavailable")
        self.assertEqual(c("Brak w magazynie"), "Unavailable")
        self.assertEqual(c("Out of stock"), "Unavailable")
        self.assertEqual(c("Dodaj do koszyka 1 999 zł"), "Available")
        self.assertEqual(c("Dostępny od ręki"), "Available")
        self.assertEqual(c("Kup teraz"), "Available")
        self.assertEqual(c(""), "Unknown")

    def test_colours(self):
        d = matching.detect_colour
        self.assertEqual(d("Redmi Note 17 Pro Max 5G 8/256GB Cloud Blush"), "Pink")
        self.assertEqual(d("17T Pro 12/512GB Deep Blue"), "Blue")
        self.assertEqual(d("Redmi 17 Czarny"), "Black")
        self.assertEqual(d("Xiaomi 17 Ultra"), "Unknown")
        self.assertEqual(ktr.get_color("Redmi 17 Cloud Blush"), "Pink")


class EditableMarkers(unittest.TestCase):

    def test_json_words_are_used(self):
        old = matching.MARKERS_FILE
        import json, tempfile, os
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.json")
            json.dump({"unavailable": ["Zniknął z oferty"], "available": []},
                      open(p, "w", encoding="utf-8"))
            matching.MARKERS_FILE = p
            try:
                self.assertEqual(
                    matching.classify_availability("Zniknal z oferty 999 zł"),
                    "Unavailable")
            finally:
                matching.MARKERS_FILE = old


if __name__ == "__main__":
    unittest.main()
