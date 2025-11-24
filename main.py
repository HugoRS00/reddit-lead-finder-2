#!/usr/bin/env python3
"""
Lead Finders for TradingWizard.ai
CLI Entry Point
"""

import json
from services.reddit_service import RedditLeadFinder
from services.x_service import XLeadFinder

def main():
    print("Starting Lead Finder Scan...")
    
    # Reddit
    try:
        reddit_finder = RedditLeadFinder()
        print("Scanning Reddit...")
        reddit_results = reddit_finder.search_reddit()
        print(f"Found {len(reddit_results)} Reddit leads")
    except Exception as e:
        print(f"Reddit scan failed: {e}")
        reddit_results = []

    # X (Twitter)
    try:
        x_finder = XLeadFinder()
        print("Scanning X...")
        x_results = x_finder.search_x()
        print(f"Found {len(x_results)} X leads")
    except Exception as e:
        print(f"X scan failed (check API keys): {e}")
        x_results = []

    # Save results
    output = {
        "reddit": reddit_results,
        "x": x_results
    }
    
    with open('leads.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Saved total {len(reddit_results) + len(x_results)} leads to leads.json")

if __name__ == "__main__":
    main()
