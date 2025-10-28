#!/usr/bin/env python3
"""
Lead Finders for TradingWizard.ai
Includes Reddit and X (Twitter) search capability.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import praw
import requests
from dotenv import load_dotenv

load_dotenv()

DEDUPE_CACHE_PATH = os.getenv('LEAD_DEDUPE_CACHE', 'lead_dedupe_cache.json')
MAX_DEDUPE_IDS = int(os.getenv('LEAD_DEDUPE_MAX_IDS', '400'))


def load_dedupe_cache() -> Dict[str, List[str]]:
    """Load deduplication cache from disk."""
    cache_file = Path(DEDUPE_CACHE_PATH)
    if not cache_file.exists():
        return {"reddit": [], "x": []}
    try:
        with cache_file.open('r') as f:
            data = json.load(f)
            return {
                "reddit": data.get("reddit", []),
                "x": data.get("x", [])
            }
    except (json.JSONDecodeError, OSError):
        return {"reddit": [], "x": []}


def save_dedupe_cache(cache: Dict[str, List[str]]) -> None:
    """Persist deduplication cache."""
    cache_file = Path(DEDUPE_CACHE_PATH)
    serializable = {
        "reddit": cache.get("reddit", [])[:MAX_DEDUPE_IDS],
        "x": cache.get("x", [])[:MAX_DEDUPE_IDS]
    }
    try:
        with cache_file.open('w') as f:
            json.dump(serializable, f, indent=2)
    except OSError as exc:
        print(f"Warning: unable to save dedupe cache: {exc}")


def merge_dedupe_ids(cache: Dict[str, List[str]], source: str, new_ids: List[str]) -> None:
    """Merge newly seen IDs into cache while enforcing uniqueness and length."""
    existing = cache.get(source, [])
    combined = [lead_id for lead_id in new_ids if lead_id] + existing
    seen = set()
    trimmed: List[str] = []
    for lead_id in combined:
        if lead_id not in seen:
            seen.add(lead_id)
            trimmed.append(lead_id)
        if len(trimmed) >= MAX_DEDUPE_IDS:
            break
    cache[source] = trimmed


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
        self.rate_snapshot: Dict[str, Dict[str, Optional[int]]] = {}
        self.context_fetch_limit = int(os.getenv('X_CONTEXT_FETCH_LIMIT', '5'))
        self._conversation_cache: Dict[str, List[Dict]] = {}

    def search_x(self, keywords: Optional[List[str]] = None, date_range_days: int = 7,
                 limit: int = 50, include_replies: bool = False,
                 min_followers: int = 0, min_engagement: int = 0) -> List[Dict]:
        """Search X (Twitter) for relevant tweets."""
        search_keywords = keywords or self.keywords
        if not search_keywords:
            return []
        self.rate_snapshot = {}

        # Build X query (top 5 keywords to stay within query length limits)
        keyword_query = " OR ".join([f'("{kw}")' for kw in search_keywords[:5]])
        language_query = ""
        if self.languages:
            # X only allows a single lang filter; use the first language preference
            language_query = f" lang:{self.languages[0]}"

        filters = ["-is:retweet"]
        if not include_replies:
            filters.append("-is:reply")

        query = " ".join(part for part in [keyword_query + language_query] + filters if part)

        params = {
            "query": query,
            "max_results": min(limit, 100),
            "tweet.fields": "author_id,created_at,public_metrics,lang,conversation_id",
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
            self._record_rate_info(response.headers, label="search")
        except requests.HTTPError as http_err:
            raise RuntimeError(f"X API returned error: {http_err.response.text}") from http_err
        except requests.RequestException as req_err:
            raise RuntimeError(f"Failed to reach X API: {req_err}") from req_err

        data = response.json()
        tweets = data.get("data", [])
        users = {user["id"]: user for user in data.get("includes", {}).get("users", [])}

        results: List[Dict] = []
        seen_conversations = set()
        context_calls = 0
        for tweet in tweets:
            convo_id = tweet.get("conversation_id")
            if convo_id and convo_id in seen_conversations:
                continue
            if convo_id:
                seen_conversations.add(convo_id)

            author = users.get(tweet["author_id"], {})
            username = author.get("username", "unknown")
            display_name = author.get("name") or username
            metrics = tweet.get("public_metrics", {})
            followers = author.get("public_metrics", {}).get("followers_count", 0)

            score = (
                metrics.get("like_count", 0)
                + (metrics.get("retweet_count", 0) * 2)
                + metrics.get("reply_count", 0)
                + metrics.get("quote_count", 0)
            )

            if followers < min_followers or score < min_engagement:
                continue

            context_snippets: List[Dict[str, str]] = []
            if convo_id:
                if convo_id in self._conversation_cache:
                    context_snippets = self._conversation_cache[convo_id]
                elif context_calls < self.context_fetch_limit:
                    context_snippets = self._fetch_conversation_context(convo_id)
                    context_calls += 1

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
                'followers': followers,
                'score': score,
                'created_utc': tweet.get("created_at", ""),
                'intent_label': LeadClassifier.classify(tweet.get("text", "")),
                'include_link': True,
                'metrics': metrics,
                'conversation_context': context_snippets
            }

            results.append(result)

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:min(limit, self.max_results)]

    def _record_rate_info(self, headers: Dict[str, str], label: str = "search") -> Dict[str, Optional[int]]:
        """Capture rate limit snapshot from X headers."""
        def safe_int(value: Optional[str]) -> Optional[int]:
            try:
                return int(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        timestamp = int(time.time())
        info = {
            "label": label,
            "limit": safe_int(headers.get("x-rate-limit-limit")),
            "remaining": safe_int(headers.get("x-rate-limit-remaining")),
            "reset_epoch": safe_int(headers.get("x-rate-limit-reset")),
            "captured_at": timestamp
        }
        if info["reset_epoch"]:
            info["resets_in"] = max(info["reset_epoch"] - timestamp, 0)

        if label == "context":
            existing = self.rate_snapshot.get("context_calls", [])
            existing = existing[:] if isinstance(existing, list) else []
            existing.append(info)
            self.rate_snapshot["context_calls"] = existing
        else:
            self.rate_snapshot[label] = info
        return info

    def _fetch_conversation_context(self, conversation_id: str) -> List[Dict[str, str]]:
        """Fetch a few recent replies for context without overusing rate limits."""
        if not conversation_id:
            return []
        if conversation_id in self._conversation_cache:
            return self._conversation_cache[conversation_id]

        params = {
            "query": f"conversation_id:{conversation_id} is:reply",
            "max_results": 5,
            "tweet.fields": "author_id,created_at,public_metrics,text",
            "user.fields": "username,name",
            "expansions": "author_id"
        }

        try:
            response = self.session.get(
                "https://api.twitter.com/2/tweets/search/recent",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            self._record_rate_info(response.headers, label="context")
        except requests.HTTPError as http_err:
            print(f"Context fetch failed for conversation {conversation_id}: {http_err.response.text}")
            self._conversation_cache[conversation_id] = []
            return []
        except requests.RequestException as req_err:
            print(f"Context fetch failed for conversation {conversation_id}: {req_err}")
            self._conversation_cache[conversation_id] = []
            return []

        data = response.json()
        replies = data.get("data", [])
        users = {user["id"]: user for user in data.get("includes", {}).get("users", [])}

        snippets: List[Dict[str, str]] = []
        for reply in replies:
            author = users.get(reply.get("author_id", ""), {})
            username = author.get("username", "unknown")
            snippet = {
                "author": f"@{username}",
                "text": reply.get("text", "")[:280],
                "created_at": reply.get("created_at", "")
            }
            snippets.append(snippet)

        self._conversation_cache[conversation_id] = snippets
        return snippets


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
