#!/usr/bin/env python3
"""
Reddit Lead Finder for TradingWizard.ai
Enhanced version with comment search and body text included
"""

import praw
import json
import os
from datetime import datetime
from typing import List, Dict
import time
from dotenv import load_dotenv

load_dotenv()

class RedditLeadFinder:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the Reddit Lead Finder with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize Reddit API
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'TradingWizard Lead Finder v2.0')
        )
        
        self.keywords = self.config.get('keywords_core', [])
    
    def search_reddit(self, keywords: List[str] = None, date_range_days: int = 7, 
                     limit: int = 50, search_comments: bool = True) -> List[Dict]:
        """Search Reddit for relevant posts and comments."""
        results = []
        cutoff_time = time.time() - (date_range_days * 86400)
        
        # Use provided keywords or default
        search_keywords = keywords or self.keywords
        
        # Default trading subreddits
        subreddits_to_search = [
            'algotrading', 'trading', 'daytrading', 'stocks', 
            'investing', 'options', 'forex', 'cryptocurrency'
        ]
        
        seen_urls = set()
        
        # Search each subreddit
        for subreddit_name in subreddits_to_search:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search posts
                for keyword in search_keywords[:5]:  # Top 5 keywords
                    try:
                        for submission in subreddit.search(keyword, time_filter='week', limit=10):
                            if submission.created_utc < cutoff_time:
                                continue
                            
                            url = f"https://reddit.com{submission.permalink}"
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)
                            
                            # Create result
                            result = {
                                'type': 'post',
                                'url': url,
                                'subreddit': subreddit_name,
                                'title': submission.title,
                                'body': submission.selftext[:500] if submission.selftext else submission.title,
                                'context': submission.selftext or submission.title,  # Full text for AI
                                'author': str(submission.author) if submission.author else '[deleted]',
                                'score': submission.score,
                                'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                                'intent_label': self._classify_intent(submission.title + " " + submission.selftext),
                                'include_link': True
                            }
                            
                            results.append(result)
                            
                            # Search comments if enabled
                            if search_comments and len(results) < limit:
                                try:
                                    submission.comments.replace_more(limit=0)
                                    for comment in submission.comments.list()[:5]:
                                        if hasattr(comment, 'body') and len(comment.body) > 100:
                                            comment_url = f"https://reddit.com{comment.permalink}"
                                            if comment_url in seen_urls:
                                                continue
                                            seen_urls.add(comment_url)
                                            
                                            comment_result = {
                                                'type': 'comment',
                                                'url': comment_url,
                                                'subreddit': subreddit_name,
                                                'title': f"Comment in: {submission.title[:50]}...",
                                                'body': comment.body[:500],
                                                'context': comment.body,  # Full text for AI
                                                'author': str(comment.author) if comment.author else '[deleted]',
                                                'score': comment.score,
                                                'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat(),
                                                'intent_label': self._classify_intent(comment.body),
                                                'include_link': True
                                            }
                                            
                                            results.append(comment_result)
                                except Exception as e:
                                    print(f"Error fetching comments: {e}")
                                    continue
                            
                    except Exception as e:
                        print(f"Error searching keyword '{keyword}': {e}")
                        continue
                        
            except Exception as e:
                print(f"Error accessing r/{subreddit_name}: {e}")
                continue
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def _classify_intent(self, text: str) -> str:
        """Classify the intent of the text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['recommend', 'best', 'looking for', 'which', 'suggest']):
            return 'Tool-seeking'
        elif any(word in text_lower for word in ['how to', 'how do', 'guide', 'help me']):
            return 'How-to'
        elif any(word in text_lower for word in ['problem', 'issue', 'stuck', 'error', 'not working']):
            return 'Problem-solving'
        else:
            return 'General discussion'


if __name__ == "__main__":
    finder = RedditLeadFinder()
    results = finder.search_reddit()
    
    with open('leads.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Found {len(results)} opportunities")