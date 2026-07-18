import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from bm25_index import BM25KeywordIndex


class BM25KeywordIndexTests(unittest.TestCase):
    def test_search_ranks_relevant_documents(self):
        docs = [
            {"id": "doc1", "text": "The constitution protects freedom of speech and arrest rights."},
            {"id": "doc2", "text": "Criminal procedure covers bail and FIR registration."},
        ]

        index = BM25KeywordIndex.from_documents(docs)
        results = index.search("arrest rights", top_k=1)

        self.assertEqual(results[0]["id"], "doc1")


if __name__ == "__main__":
    unittest.main()
