import os
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
import praw
from .utils import LeadClassifier

class RedditLeadFinder:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the Reddit Lead Finder with configuration."""
        self.config = {}
        if os.path.exists(config_path):
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
                # Limit keywords to avoid too many API calls if list is long
                for keyword in search_keywords[:5]: 
                    try:
                        # Use 'new' or 'relevance' depending on needs, 'relevance' usually better for keywords
                        # time_filter='week' is good default
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
                                'source': 'reddit',
                                'id': submission.id,
                                'url': url,
                                'subreddit': subreddit_name,
                                'title': submission.title,
                                'body': submission.selftext[:500] if submission.selftext else submission.title,
                                'context': submission.selftext or submission.title,  # Full text for AI
                                'author': str(submission.author) if submission.author else '[deleted]',
                                'score': submission.score,
                                'created_utc': datetime.utcfromtimestamp(submission.created_utc).isoformat() + 'Z',
                                'intent_label': LeadClassifier.classify(f"{submission.title} {submission.selftext}"),
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
                                                'source': 'reddit',
                                                'id': comment.id,
                                                'url': comment_url,
                                                'subreddit': subreddit_name,
                                                'title': f"Comment in: {submission.title[:50]}...",
                                                'body': comment.body[:500],
                                                'context': comment.body,  # Full text for AI
                                                'author': str(comment.author) if comment.author else '[deleted]',
                                                'score': comment.score,
                                                'created_utc': datetime.utcfromtimestamp(comment.created_utc).isoformat() + 'Z',
                                                'intent_label': LeadClassifier.classify(comment.body),
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
