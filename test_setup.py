#!/usr/bin/env python3
"""
Test script to verify Reddit Lead Finder v2.0 setup
"""

import os
import sys

def test_imports():
    """Test if all required packages are installed."""
    print("🔍 Testing imports...")
    try:
        import flask
        print("  ✅ Flask")
        import praw
        print("  ✅ PRAW")
        import anthropic
        print("  ✅ Anthropic")
        from dotenv import load_dotenv
        print("  ✅ python-dotenv")
        print("✅ All imports successful!\n")
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        print("Run: pip install -r requirements.txt\n")
        return False

def test_config():
    """Test if config.json exists and is valid."""
    print("🔍 Testing configuration...")
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("  ✅ config.json found and valid")
        print(f"  📊 {len(config.get('keywords_core', []))} core keywords configured")
        return True
    except Exception as e:
        print(f"  ❌ Config error: {e}\n")
        return False

def test_env():
    """Test if .env file exists."""
    print("🔍 Testing environment variables...")
    if not os.path.exists('.env'):
        print("  ⚠️  .env file not found")
        print("  Run: cp .env.example .env")
        print("  Then add your Reddit credentials\n")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not client_id or client_id == 'your_client_id_here':
        print("  ❌ REDDIT_CLIENT_ID not set\n")
        return False
    
    if not client_secret or client_secret == 'your_client_secret_here':
        print("  ❌ REDDIT_CLIENT_SECRET not set\n")
        return False
    
    print("  ✅ REDDIT_CLIENT_ID set")
    print("  ✅ REDDIT_CLIENT_SECRET set")
    
    if anthropic_key and anthropic_key != 'your_anthropic_api_key_here':
        print("  ✅ ANTHROPIC_API_KEY set (AI replies enabled)")
    else:
        print("  ⚠️  ANTHROPIC_API_KEY not set (will use templates)")
    
    print("✅ Environment configured!\n")
    return True

def test_reddit_connection():
    """Test Reddit API connection."""
    print("🔍 Testing Reddit API connection...")
    try:
        import praw
        from dotenv import load_dotenv
        load_dotenv()
        
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'Test')
        )
        
        # Try to access a subreddit
        subreddit = reddit.subreddit('test')
        subreddit.id
        
        print("  ✅ Reddit API connection successful")
        print("✅ Reddit API working!\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Reddit API error: {str(e)}")
        print("  Check your credentials in .env\n")
        return False

def test_flask():
    """Test if Flask can start."""
    print("🔍 Testing Flask application...")
    try:
        from app import app
        print("  ✅ Flask app imported successfully")
        print("✅ Flask application ready!\n")
        return True
    except Exception as e:
        print(f"  ❌ Flask error: {str(e)}\n")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Reddit Lead Finder v2.0 - Setup Test")
    print("=" * 60)
    print()
    
    tests = [
        test_imports,
        test_config,
        test_env,
        test_reddit_connection,
        test_flask
    ]
    
    results = [test() for test in tests]
    
    print("=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED!")
        print("\nYou're ready to go!")
        print("\nTo start the app:")
        print("  python app.py")
        print("\nThen open: http://localhost:5000")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the issues above and run this test again.")
    print("=" * 60)
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
