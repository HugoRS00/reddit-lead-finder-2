#!/usr/bin/env python3
"""
Lead Finders for TradingWizard.ai
Includes Reddit and X (Twitter) search capability.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import praw
import requests
from dotenv import load_dotenv

load_dotenv()

class LeadClassifier:
    """Utility class to classify lead intent text."""

    @staticmethod
    def classify(text: str) -> str:
        text_lower = text.lower()

        if any(word in text_lower for word in ['recommend', 'best', 'looking for', 'which', 'suggest']):
            return 'Tool-seeking'
        if any(word in text_lower for word in ['how to', 'how do', 'guide', 'help me']):
            return 'How-to'
        if any(word in text_lower for word in ['problem', 'issue', 'stuck', 'error', 'not working']):
            return 'Problem-solving'
        return 'General discussion'


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


class XLeadFinder:
    """Lead finder for X (Twitter) using the v2 Recent Search API."""

    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        token = os.getenv('X_BEARER_TOKEN') or os.getenv('TWITTER_BEARER_TOKEN')
        if not token:
            raise ValueError("X_BEARER_TOKEN or TWITTER_BEARER_TOKEN must be set for X lead search")

        self.bearer_token = token
        self.keywords = self.config.get('keywords_core', [])
        self.languages = self.config.get('languages', ['en'])
        self.max_results = self.config.get('max_results', 50)

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bearer_token}"
        })

    def search_x(self, keywords: Optional[List[str]] = None, date_range_days: int = 7,
                 limit: int = 50) -> List[Dict]:
        """Search X (Twitter) for relevant tweets."""
        search_keywords = keywords or self.keywords
        if not search_keywords:
            return []

        # Build X query (top 5 keywords to stay within query length limits)
        keyword_query = " OR ".join([f'("{kw}")' for kw in search_keywords[:5]])
        language_query = ""
        if self.languages:
            # X only allows a single lang filter; use the first language preference
            language_query = f" lang:{self.languages[0]}"

        query = f"{keyword_query}{language_query} -is:retweet"

        params = {
            "query": query,
            "max_results": min(limit, 100),
            "tweet.fields": "author_id,created_at,public_metrics,lang",
            "user.fields": "username,name,public_metrics",
            "expansions": "author_id"
        }

        if date_range_days:
            start_time = datetime.now(timezone.utc) - timedelta(days=min(date_range_days, 7))
            params["start_time"] = start_time.isoformat().replace("+00:00", "Z")

        try:
            response = self.session.get(
                "https://api.twitter.com/2/tweets/search/recent",
                params=params,
                timeout=15
            )
            response.raise_for_status()
        except requests.HTTPError as http_err:
            raise RuntimeError(f"X API returned error: {http_err.response.text}") from http_err
        except requests.RequestException as req_err:
            raise RuntimeError(f"Failed to reach X API: {req_err}") from req_err

        data = response.json()
        tweets = data.get("data", [])
        users = {user["id"]: user for user in data.get("includes", {}).get("users", [])}

        results: List[Dict] = []
        for tweet in tweets:
            author = users.get(tweet["author_id"], {})
            username = author.get("username", "unknown")
            display_name = author.get("name") or username
            metrics = tweet.get("public_metrics", {})

            score = (
                metrics.get("like_count", 0)
                + (metrics.get("retweet_count", 0) * 2)
                + metrics.get("reply_count", 0)
                + metrics.get("quote_count", 0)
            )

            result = {
                'type': 'tweet',
                'source': 'x',
                'id': tweet["id"],
                'url': f"https://twitter.com/{username}/status/{tweet['id']}",
                'title': f"Tweet by {display_name}",
                'body': tweet.get("text", "")[:500],
                'context': tweet.get("text", ""),
                'author': f"@{username}",
                'author_name': display_name,
                'score': score,
                'created_utc': tweet.get("created_at", ""),
                'intent_label': LeadClassifier.classify(tweet.get("text", "")),
                'include_link': True,
                'metrics': metrics
            }

            results.append(result)

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:min(limit, self.max_results)]


if __name__ == "__main__":
    finder = RedditLeadFinder()
    reddit_results = finder.search_reddit()

    try:
        x_finder = XLeadFinder()
        x_results = x_finder.search_x()
    except Exception as e:
        print(f"X finder not initialized: {e}")
        x_results = []

    with open('leads.json', 'w') as f:
        json.dump({
            "reddit": reddit_results,
            "x": x_results
        }, f, indent=2)

    print(f"Found {len(reddit_results)} Reddit opportunities and {len(x_results)} X opportunities")
