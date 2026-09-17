import unittest

from gbbo.wikitext import iter_table_rows, strip_markup, strip_templates


class TemplateUnwrap(unittest.TestCase):
    def test_nowrap_keeps_piped_wikilink(self):
        raw = "{{nowrap|[[Carol Li|Pui Man]]}}"
        self.assertEqual(strip_templates(raw), "[[Carol Li|Pui Man]]")
        self.assertEqual(strip_markup(raw), "Pui Man")

    def test_sort_template_does_not_eat_table_end(self):
        # Innermost {{sort|1|}} used to look like a table closer.
        text = "{{sort|1|Jasmine}}"
        self.assertEqual(strip_templates(text), "Jasmine")


class TableRows(unittest.TestCase):
    def test_inserts_row_marker_when_missing(self):
        table = """{| class="wikitable"
! Baker !! Age
|-
! Jairzinho || 51
|}"""
        rows = list(iter_table_rows(table))
        self.assertGreaterEqual(len(rows), 2)
        self.assertTrue(any("Jairzinho" in "".join(r) for r in rows))


if __name__ == "__main__":
    unittest.main()
