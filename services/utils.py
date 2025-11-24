class LeadClassifier:
    """Utility class to classify lead intent text."""

    @staticmethod
    def classify(text: str) -> str:
        text_lower = text.lower()

        if any(word in text_lower for word in ['recommend', 'best', 'looking for', 'which', 'suggest']):
            return 'Tool-seeking'
        if any(word in text_lower for word in ['how to', 'how do', 'guide', 'help me']):
            return 'How-to'
        if any(word in text_lower for word in ['problem', 'issue', 'stuck', 'error', 'not working', 'broken', 'fail', 'crash']):
            return 'Problem-solving'
        return 'General discussion'
