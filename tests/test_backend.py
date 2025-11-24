import unittest
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reddit_service import RedditLeadFinder
from services.x_service import XLeadFinder
from services.ai_service import AIService
from services.utils import LeadClassifier

class TestBackend(unittest.TestCase):
    def test_imports(self):
        """Test that services can be imported."""
        self.assertTrue(RedditLeadFinder)
        self.assertTrue(XLeadFinder)
        self.assertTrue(AIService)

    def test_classifier(self):
        """Test intent classification."""
        self.assertEqual(LeadClassifier.classify("How do I use this?"), "How-to")
        self.assertEqual(LeadClassifier.classify("Best tool for trading?"), "Tool-seeking")
        self.assertEqual(LeadClassifier.classify("My bot is broken"), "Problem-solving")
        self.assertEqual(LeadClassifier.classify("Just chatting"), "General discussion")

if __name__ == '__main__':
    unittest.main()
