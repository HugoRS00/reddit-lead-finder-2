import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIService

class TestAIVoice(unittest.TestCase):
    def test_default_voice_instructions(self):
        """Test that default voice instructions are applied when none provided."""
        service = AIService()
        # Mock the client to avoid actual API calls
        service.client = MagicMock()
        service.client.messages.create.return_value.content = [MagicMock(text="Test reply")]
        
        # Call generate_reply without voice profile
        service.generate_reply("Context", "Intent", "full", "medium", None)
        
        # Check if the prompt contained the new default instructions
        call_args = service.client.messages.create.call_args
        prompt_sent = call_args[1]['messages'][0]['content']
        
        self.assertIn("strictly lowercase", prompt_sent)
        self.assertIn("minimal punctuation", prompt_sent)
        self.assertIn("structure: 1. the read", prompt_sent)

if __name__ == '__main__':
    unittest.main()
