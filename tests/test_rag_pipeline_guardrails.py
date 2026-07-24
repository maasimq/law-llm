import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from rag_pipeline import is_out_of_scope_question


class RagPipelineGuardrailTests(unittest.TestCase):
    def test_constitutional_question_is_not_flagged_out_of_scope(self):
        question = "What does Article 10 say about arrest and detention?"
        self.assertFalse(is_out_of_scope_question(question, filter_act="Constitution of Pakistan"))

    def test_non_constitutional_tax_question_is_flagged_out_of_scope(self):
        question = "What is the corporate tax rate on rental income under Pakistani law?"
        self.assertTrue(is_out_of_scope_question(question, filter_act="Constitution of Pakistan"))

    def test_non_constitutional_criminal_question_is_flagged_out_of_scope(self):
        question = "What are the criminal penalties for theft under the PPC?"
        self.assertTrue(is_out_of_scope_question(question, filter_act="Constitution of Pakistan"))


if __name__ == "__main__":
    unittest.main()
