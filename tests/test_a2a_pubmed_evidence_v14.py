import unittest
import xml.etree.ElementTree as ET

from track3_a2a.acquire_pubmed_evidence_v14 import parse_article


class A2APubmedEvidenceV14Tests(unittest.TestCase):
    def test_pubmed_xml_parser_preserves_structured_abstract_and_identifiers(self):
        node = ET.fromstring("""
        <PubmedArticle>
          <MedlineCitation>
            <PMID>123</PMID>
            <Article>
              <ArticleTitle>A2A functional study</ArticleTitle>
              <Abstract><AbstractText Label="RESULTS">cAMP increased.</AbstractText></Abstract>
              <Journal><Title>Test Journal</Title></Journal>
              <PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>
            </Article>
          </MedlineCitation>
          <PubmedData><ArticleIdList>
            <ArticleId IdType="doi">10.1/test</ArticleId>
            <ArticleId IdType="pmc">PMC123</ArticleId>
          </ArticleIdList></PubmedData>
        </PubmedArticle>
        """)
        result = parse_article(node)
        self.assertEqual(result["pmid"], "123")
        self.assertEqual(result["abstract"], "RESULTS: cAMP increased.")
        self.assertEqual(result["doi"], "10.1/test")
        self.assertEqual(result["pmcid"], "PMC123")


if __name__ == "__main__":
    unittest.main()
