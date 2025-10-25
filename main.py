#!/usr/bin/env python3
"""
Reddit Lead Finder v2.0 - Enhanced with comment search
"""

import praw
import json
import os
from datetime import datetime
from typing import List, Dict
import re
from collections import defaultdict
import time

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
        
        # Expand keywords automatically
        self.keywords = self._expand_keywords()
        
    def _expand_keywords(self) -> List[str]:
        """Expand core keywords with variants and intent phrases."""
        core = self.config.get('keywords_core', [])
        expanded = core.copy()
        
        variations = [
            "best {} for",
            "recommend {}",
            "looking for {}",
            "any good {}",
            "help with {}",
            "{} recommendations",
            "{} tool",
            "{} platform",
            "AI for trading",
            "trading bot",
            "chart analysis",
            "technical analysis",
            "algo trading",
            "backtest platform",
            "trading signals"
        ]
        
        for keyword in core[:3]:
            for var in variations[:8]:
                if '{}' in var:
                    expanded.append(var.format(keyword))
        
        intent_phrases = [
            "how do I analyze charts",
            "need trading tool",
            "automate my trading",
            "technical analysis help",
            "trading tool recommendations",
            "chart analyzer",
            "stock analyzer",
            "crypto analyzer",
            "forex analyzer"
        ]
        expanded.extend(intent_phrases)
        
        return list(set(expanded))[:50]
    
    def _calculate_relevance_score(self, text: str, title: str, subreddit: str, 
                                   created_utc: int, upvotes: int) -> tuple:
        """Calculate relevance score (0-100) based on multiple factors."""
        text_lower = (text + " " + title).lower()
        
        # Intent match (40%)
        intent_patterns = {
            'tool-seeking': r'(recommend|best|looking for|suggest|which|what.*use|any good|need.*tool)',
            'how-to': r'(how to|how do|how can|guide|tutorial|help me|teach)',
            'problem-solving': r'(problem|issue|stuck|struggling|confused|not working|error)',
            'show-and-tell': r'(built|made|created|check out|my.*tool)',
        }
        
        intent_label = "General discussion"
        intent_score = 20
        
        for label, pattern in intent_patterns.items():
            if re.search(pattern, text_lower):
                intent_label = label.title().replace('-', ' ')
                intent_score = 40
                break
        
        # Keyword density (20%)
        matched_keywords = []
        keyword_score = 0
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
                keyword_score += 2
        keyword_score = min(keyword_score, 20)
        
        # Context fit (25%)
        feature_keywords = ['chart', 'technical analysis', 'AI', 'automat', 'algo', 
                          'signal', 'backtest', 'scan', 'indicator', 'strategy',
                          'crypto', 'stock', 'forex', 'analyze']
        context_score = sum(5 for kw in feature_keywords if kw in text_lower)
        context_score = min(context_score, 25)
        
        # Freshness (10%)
        age_days = (time.time() - created_utc) / 86400
        if age_days < 1:
            freshness_score = 10
        elif age_days < 3:
            freshness_score = 7
        elif age_days < 7:
            freshness_score = 5
        else:
            freshness_score = 0
        
        # Subreddit quality (5%)
        quality_subs = ['algotrading', 'trading', 'daytrading', 'stocks', 'investing', 
                       'wallstreetbets', 'forex', 'cryptocurrency', 'bitcoin', 'cryptotrading']
        subreddit_score = 5 if any(sub in subreddit.lower() for sub in quality_subs) else 3
        
        total_score = intent_score + keyword_score + context_score + freshness_score + subreddit_score
        
        return total_score, intent_label, matched_keywords
    
    def _assess_risks(self, subreddit: str, text: str) -> List[str]:
        """Identify risk flags for the opportunity."""
        risks = []
        
        strict_subs = ['wallstreetbets', 'investing', 'stocks']
        if any(sub in subreddit.lower() for sub in strict_subs):
            risks.append("self-promo restricted")
        
        spam_indicators = ['giveaway', 'free money', 'guaranteed', '100% win', 'get rich']
        if any(indicator in text.lower() for indicator in spam_indicators):
            risks.append("low-quality thread")
        
        return risks
    
    def search_reddit(self, keywords: List[str] = None, date_range_days: int = 7, 
                     limit: int = 50, search_comments: bool = True) -> List[Dict]:
        """Search Reddit for relevant opportunities in both posts and comments."""
        results = []
        cutoff_time = time.time() - (date_range_days * 86400)
        
        # Use provided keywords or default
        search_keywords = keywords if keywords else self.keywords[:10]
        
        # Determine subreddits
        allowlist = self.config.get('allowlist_subs', [])
        blocklist = self.config.get('blocklist_subs', [])
        
        if allowlist:
            subreddits_to_search = allowlist
        else:
            subreddits_to_search = [
                'algotrading', 'trading', 'daytrading', 'stocks', 'investing',
                'options', 'forex', 'cryptocurrency', 'cryptotrading', 'bitcoin'
            ]
        
        subreddits_to_search = [s for s in subreddits_to_search if s not in blocklist]
        
        print(f"🔍 Searching {len(subreddits_to_search)} subreddits...")
        
        for subreddit_name in subreddits_to_search:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search posts
                for keyword in search_keywords:
                    try:
                        for submission in subreddit.search(keyword, time_filter='week', limit=5):
                            if submission.created_utc < cutoff_time:
                                continue
                            
                            if submission.score < 3:
                                continue
                            
                            score, intent, matched = self._calculate_relevance_score(
                                submission.selftext,
                                submission.title,
                                subreddit_name,
                                submission.created_utc,
                                submission.score
                            )
                            
                            if score < 60:
                                continue
                            
                            risks = self._assess_risks(subreddit_name, 
                                                      submission.title + " " + submission.selftext)
                            
                            hard_risks = ["low-quality thread"]
                            if any(r in risks for r in hard_risks):
                                continue
                            
                            include_link = "self-promo restricted" not in risks
                            
                            result = {
                                'url': f"https://reddit.com{submission.permalink}",
                                'type': 'post',
                                'subreddit': f"r/{subreddit_name}",
                                'title': submission.title,
                                'content': submission.selftext[:500] if submission.selftext else submission.title,
                                'author': f"u/{submission.author.name if submission.author else '[deleted]'}",
                                'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                                'upvotes': submission.score,
                                'matched_keywords': matched[:5],
                                'intent_label': intent,
                                'relevance_score': score,
                                'risk_flags': risks,
                                'include_link': include_link,
                                'context': submission.selftext[:1000] if submission.selftext else submission.title
                            }
                            
                            results.append(result)
                    except Exception as e:
                        print(f"Error searching posts in r/{subreddit_name}: {e}")
                        continue
                
                # Search comments (NEW!)
                if search_comments:
                    for keyword in search_keywords[:5]:  # Limit keywords for comments
                        try:
                            for comment in subreddit.comments(limit=20):
                                if not comment.body or comment.created_utc < cutoff_time:
                                    continue
                                
                                if comment.score < 2:
                                    continue
                                
                                # Check if keyword matches
                                if keyword.lower() not in comment.body.lower():
                                    continue
                                
                                score, intent, matched = self._calculate_relevance_score(
                                    comment.body,
                                    "",
                                    subreddit_name,
                                    comment.created_utc,
                                    comment.score
                                )
                                
                                if score < 60:
                                    continue
                                
                                risks = self._assess_risks(subreddit_name, comment.body)
                                
                                hard_risks = ["low-quality thread"]
                                if any(r in risks for r in hard_risks):
                                    continue
                                
                                include_link = "self-promo restricted" not in risks
                                
                                result = {
                                    'url': f"https://reddit.com{comment.permalink}",
                                    'type': 'comment',
                                    'subreddit': f"r/{subreddit_name}",
                                    'title': f"Comment in: {comment.submission.title[:100]}...",
                                    'content': comment.body[:500],
                                    'author': f"u/{comment.author.name if comment.author else '[deleted]'}",
                                    'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat(),
                                    'upvotes': comment.score,
                                    'matched_keywords': matched[:5],
                                    'intent_label': intent,
                                    'relevance_score': score,
                                    'risk_flags': risks,
                                    'include_link': include_link,
                                    'context': comment.body[:1000]
                                }
                                
                                results.append(result)
                        except Exception as e:
                            print(f"Error searching comments in r/{subreddit_name}: {e}")
                            continue
                        
            except Exception as e:
                print(f"Error accessing r/{subreddit_name}: {e}")
                continue
        
        # Sort and deduplicate
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        seen_urls = set()
        unique_results = []
        for result in results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        return unique_results[:limit]
    
    def run(self, keywords: List[str] = None, output_file: str = 'leads.json'):
        """Run the lead finder and save results."""
        print("🔍 Starting Reddit Lead Finder v2.0 for TradingWizard.ai...")
        print(f"📊 Searching with {len(self.keywords)} keywords...")
        
        results = self.search_reddit(keywords=keywords)
        
        print(f"✅ Found {len(results)} qualified opportunities")
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to {output_file}")
        
        return results


if __name__ == "__main__":
    finder = RedditLeadFinder()
    finder.run()
