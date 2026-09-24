"""
test_pipeline.py - Automated verification of ChronoLit AI components
Tests the NLP processor, Date extraction, Timeline sorter, Summarizer, and Database.
"""

import unittest
from datetime import datetime
from nlp_processor import clean_text, split_sentences, looks_like_event, event_candidates
from timeline import extract_date, make_event, sort_events
from summarizer import relevance_score, rank_candidates, generate_summary
from database import init_db, save_topic, save_events, get_all_topics, get_topic_timeline
from pipeline import run_pipeline, cluster_events

class TestChronoLitAI(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_text_cleaning(self):
        raw = "Mahatma Gandhi was born in 1869.[1][2]   He led the salt march. \n\n"
        cleaned = clean_text(raw)
        self.assertNotIn("[1]", cleaned)
        self.assertNotIn("[2]", cleaned)
        self.assertEqual(cleaned, "Mahatma Gandhi was born in 1869. He led the salt march.")

    def test_looks_like_event(self):
        self.assertTrue(looks_like_event("He was born on October 2, 1869 in Porbandar."))
        self.assertTrue(looks_like_event("In 1915, he returned to India from South Africa."))
        self.assertTrue(looks_like_event("He graduated with honors."))
        
        self.assertFalse(looks_like_event("This is a simple generic text with nothing."))

    def test_date_extraction_and_sorting(self):
        s1 = "In 1948, Mahatma Gandhi died."
        s2 = "In 1869, he was born."
        s3 = "He inspired movements across the globe with no specific year."

        e1 = make_event(s1)
        e2 = make_event(s2)
        e3 = make_event(s3)

        self.assertEqual(e1["date"].year, 1948)
        self.assertEqual(e2["date"].year, 1869)
        self.assertIsNone(e3["date"])

        sorted_ev = sort_events([e1, e2, e3])
        
        self.assertEqual(sorted_ev[0]["date"].year, 1869)
        self.assertEqual(sorted_ev[1]["date"].year, 1948)
        self.assertIsNone(sorted_ev[2]["date"])

    def test_summarizer(self):
        events = [
            {"date": datetime(1869, 1, 1), "text": "Gandhi was born in Porbandar."},
            {"date": datetime(1915, 1, 1), "text": "Returned to India and joined the freedom struggle."},
            {"date": datetime(1948, 1, 1), "text": "He died in New Delhi."}
        ]
        summary = generate_summary(events)
        self.assertEqual(len(summary), 3)
        self.assertTrue(summary[0].startswith("1869:"))
        self.assertTrue(summary[2].startswith("1948:"))

    def test_database_crud(self):
        topic_id = save_topic("Test Persona", "https://en.wikipedia.org/wiki/Test_Persona")
        self.assertIsInstance(topic_id, int)

        events = [
            {"date": datetime(1920, 1, 1), "text": "Launched movement.", "cluster": 0},
            {"date": None, "text": "Wrote letters.", "cluster": -1}
        ]
        save_events(topic_id, events)

        retrieved = get_topic_timeline(topic_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["topic"], "Test Persona")
        self.assertEqual(len(retrieved["events"]), 2)

    def test_empty_topic_validation(self):
        with self.assertRaises(ValueError):
            run_pipeline("")

if __name__ == "__main__":
    unittest.main()
