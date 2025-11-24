import os
import time
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from .utils import LeadClassifier

class XLeadFinder:
    """Lead finder for X (Twitter) using the v2 Recent Search API."""

    def __init__(self, config_path: str = "config.json"):
        self.config = {}
        if os.path.exists(config_path):
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
