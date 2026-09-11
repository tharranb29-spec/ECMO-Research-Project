import unittest

from track3_a2a.acquire_pmc_fulltext_v14 import xml_to_text


class A2APmcFulltextV14Tests(unittest.TestCase):
    def test_fulltext_parser_extracts_title_and_body_paragraphs(self):
        raw = b"""
        <article><front><article-meta><title-group><article-title>A2A study</article-title></title-group>
        </article-meta></front><body><sec><p>First <italic>functional</italic> paragraph.</p>
        <p>Second paragraph.</p></sec></body></article>
        """
        title, body = xml_to_text(raw)
        self.assertEqual(title, "A2A study")
        self.assertIn("First functional paragraph.", body)
        self.assertIn("Second paragraph.", body)


if __name__ == "__main__":
    unittest.main()
