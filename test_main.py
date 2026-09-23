import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
import main  # noqa: E402


class BriefingTests(unittest.TestCase):
    def setUp(self):
        self.item = {
            "key": "abc",
            "category": "hardware",
            "source": "Test Source",
            "title": "New CPU with DDR5 memory support",
            "summary": "A test RSS summary.",
            "url": "https://example.com/story",
            "published": datetime(2026, 9, 23, 1, 0, tzinfo=timezone.utc).isoformat(),
            "score": 3,
        }

    def test_briefing_contains_categories_and_source(self):
        text = main.build_briefing([self.item], {})
        self.assertIn("電腦硬件", text)
        self.assertIn("手機與應用程式", text)
        self.assertIn("Test Source", text)
        self.assertIn("https://example.com/story", text)

    def test_url_normalization_removes_tracking(self):
        normalized = main.normalize_url("HTTPS://Example.COM/story/?utm_source=x&ref=home&id=2#section")
        self.assertEqual(normalized, "https://example.com/story?id=2")

    @patch.dict(os.environ, {}, clear=True)
    def test_send_requires_credentials(self):
        with self.assertRaises(RuntimeError):
            main.main()

    def test_message_splitting_limit(self):
        long_item = dict(self.item, summary="x" * 1500)
        text = main.build_briefing([long_item] * 6, {})
        chunks = []
        while len(text) > 3900:
            cut = text.rfind("\n\n", 0, 3900)
            cut = cut if cut > 500 else text.rfind("\n", 0, 3900)
            cut = cut if cut > 0 else 3900
            chunks.append(text[:cut].strip())
            text = text[cut:].lstrip()
        chunks.append(text)
        self.assertTrue(all(len(chunk) <= 3900 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
