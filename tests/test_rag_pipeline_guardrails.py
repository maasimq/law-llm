import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from rag_pipeline import is_conversational, detect_language, detect_act_from_query


class RagPipelineGuardrailTests(unittest.TestCase):
    def test_conversational_queries_detected(self):
        self.assertTrue(is_conversational("Hello"))
        self.assertTrue(is_conversational("Hi, who are you?"))
        self.assertTrue(is_conversational("Thank you!"))

    def test_legal_queries_not_conversational(self):
        self.assertFalse(is_conversational("What is the punishment for theft?"))
        self.assertFalse(is_conversational("How to apply for bail under CrPC 497?"))
        self.assertFalse(is_conversational("Article 10 of the Constitution"))

    def test_language_detection(self):
        self.assertEqual(detect_language("What is theft punishment?"), "english")
        self.assertEqual(detect_language("چوری کی سزا کیا ہے؟"), "urdu")
        self.assertEqual(detect_language("chori ki saza kia hai?"), "urdu")

    def test_act_detection(self):
        self.assertEqual(detect_act_from_query("PPC Section 302"), "Pakistan Penal Code, 1860")
        self.assertEqual(detect_act_from_query("CrPC Section 497"), "Code of Criminal Procedure, 1898")
        self.assertEqual(detect_act_from_query("Article 10A of Constitution"), "Constitution of Pakistan")


if __name__ == "__main__":
    unittest.main()
