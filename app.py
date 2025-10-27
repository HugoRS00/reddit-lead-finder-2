#!/usr/bin/env python3
"""
Reddit Lead Finder - Web Dashboard
Flask web interface with all the new features
"""

from flask import Flask, render_template, jsonify, request, send_file
import json
import os
from datetime import datetime
from main import RedditLeadFinder
import sqlite3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database setup
def init_db():
    """Initialize SQLite database for lead tracking"""
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (id TEXT PRIMARY KEY,
                  url TEXT,
                  title TEXT,
                  subreddit TEXT,
                  status TEXT DEFAULT 'new',
                  notes TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  data TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan():
    """Run a new Reddit scan"""
    try:
        data = request.json
        date_range = data.get('date_range_days', 7)
        max_results = data.get('max_results', 25)
        
        finder = RedditLeadFinder()
        results = finder.search_reddit(date_range_days=date_range, limit=max_results)
        
        # Save to database
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        for result in results:
            lead_id = result['url'].split('/')[-3]  # Extract post ID from URL
            c.execute('''INSERT OR REPLACE INTO leads (id, url, title, subreddit, status, data)
                         VALUES (?, ?, ?, ?, COALESCE((SELECT status FROM leads WHERE id=?), 'new'), ?)''',
                      (lead_id, result['url'], result['title'], result['subreddit'], lead_id, json.dumps(result)))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'count': len(results), 'leads': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads with filters"""
    status = request.args.get('status', 'all')
    intent = request.args.get('intent', 'all')
    min_score = int(request.args.get('min_score', 0))
    max_score = int(request.args.get('max_score', 100))
    sort_by = request.args.get('sort_by', 'score')
    
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    
    query = 'SELECT * FROM leads WHERE 1=1'
    params = []
    
    if status != 'all':
        query += ' AND status = ?'
        params.append(status)
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    leads = []
    for row in rows:
        lead_data = json.loads(row[8])  # data column
        
        # Apply filters
        if lead_data['relevance_score'] < min_score or lead_data['relevance_score'] > max_score:
            continue
        if intent != 'all' and lead_data['intent_label'].lower() != intent.lower():
            continue
        
        lead_data['db_status'] = row[4]
        lead_data['db_notes'] = row[5]
        lead_data['db_id'] = row[0]
        leads.append(lead_data)
    
    # Sort
    if sort_by == 'score':
        leads.sort(key=lambda x: x['relevance_score'], reverse=True)
    elif sort_by == 'date':
        leads.sort(key=lambda x: x['created_utc'], reverse=True)
    
    return jsonify({'leads': leads})

@app.route('/api/leads/<lead_id>/status', methods=['POST'])
def update_status(lead_id):
    """Update lead status"""
    data = request.json
    status = data.get('status')
    notes = data.get('notes', '')
    
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('UPDATE leads SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
              (status, notes, lead_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/generate-reply', methods=['POST'])
def generate_reply():
    """Generate reply with custom parameters"""
    data = request.json
    context = data.get('context', '')
    intent = data.get('intent', 'General discussion')
    mode = data.get('mode', 'full')  # ghost, soft, full
    tone = data.get('tone', 0.5)  # 0 = casual, 1 = professional
    length = data.get('length', 'medium')  # short, medium, long
    variants = data.get('variants', 3)  # A, B, C
    
    finder = RedditLeadFinder()
    
    # Adjust include_link based on mode
    include_link = mode == 'full'
    
    # Generate base replies
    base_replies = finder._generate_reply_drafts(context, intent, include_link)
    
    # Adjust for tone and length
    replies = []
    for i in range(variants):
        if i < len(base_replies):
            reply = base_replies[i]['reply_text']
        else:
            # Generate additional variant
            reply = base_replies[i % len(base_replies)]['reply_text']
        
        # Adjust for mode
        if mode == 'ghost':
            # Remove any mention of TradingWizard
            reply = reply.split('If you want')[0].strip()
            reply = reply.split('We built')[0].strip()
            reply = reply.split('I work on')[0].strip()
            reply = reply.split('Tools that')[0].strip()
            reply = reply.split('There are platforms')[0].strip()
        elif mode == 'soft':
            # Mention name but no link
            reply = reply.replace('TradingWizard.ai', 'TradingWizard AI')
            reply = reply.replace('.ai', '')
        
        # Adjust for tone (0=casual, 1=professional)
        if tone > 0.7:
            # More professional
            reply = reply.replace("you're", "you are")
            reply = reply.replace("don't", "do not")
            reply = reply.replace("can't", "cannot")
        elif tone < 0.3:
            # More casual
            reply = reply.replace(". ", "—")[:len(reply)]  # Some dashes for casual feel
        
        # Adjust for length
        if length == 'short':
            # Take first 2 sentences
            sentences = reply.split('. ')
            reply = '. '.join(sentences[:2]) + '.'
        elif length == 'long':
            # Add more detail
            if i == 0:
                reply += " Another tip: start with just 1-2 markets and 1 timeframe to build consistency."
        
        replies.append({
            'variant': chr(65 + i),
            'reply_text': reply.strip()
        })
    
    return jsonify({'replies': replies})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    
    # Total leads
    c.execute('SELECT COUNT(*) FROM leads')
    total = c.fetchone()[0]
    
    # By status
    c.execute('SELECT status, COUNT(*) FROM leads GROUP BY status')
    by_status = dict(c.fetchall())
    
    # Average score
    c.execute('SELECT data FROM leads')
    scores = []
    subreddits = {}
    intents = {}
    
    for row in c.fetchall():
        lead = json.loads(row[0])
        scores.append(lead['relevance_score'])
        subreddit = lead['subreddit']
        subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
        intent = lead['intent_label']
        intents[intent] = intents.get(intent, 0) + 1
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    conn.close()
    
    return jsonify({
        'total': total,
        'by_status': by_status,
        'avg_score': round(avg_score, 1),
        'top_subreddits': dict(sorted(subreddits.items(), key=lambda x: x[1], reverse=True)[:5]),
        'by_intent': intents
    })

@app.route('/api/check-spam', methods=['POST'])
def check_spam():
    """Check if reply looks spammy"""
    data = request.json
    reply = data.get('reply', '')
    
    spam_score = 0
    warnings = []
    
    # Check for spam indicators
    spam_words = ['guaranteed', 'free money', 'click here', 'limited time', 'act now', '100%', 'risk-free']
    for word in spam_words:
        if word.lower() in reply.lower():
            spam_score += 20
            warnings.append(f"Contains spam word: '{word}'")
    
    # Check for excessive caps
    caps_ratio = sum(1 for c in reply if c.isupper()) / len(reply) if reply else 0
    if caps_ratio > 0.3:
        spam_score += 15
        warnings.append("Too many capital letters")
    
    # Check for excessive punctuation
    if reply.count('!') > 2:
        spam_score += 10
        warnings.append("Too many exclamation marks")
    
    # Check link density
    link_count = reply.count('http')
    if link_count > 1:
        spam_score += 15
        warnings.append("Multiple links detected")
    
    # Check for value-first content
    if len(reply) < 50:
        spam_score += 10
        warnings.append("Reply too short - add more value")
    
    spam_level = 'low' if spam_score < 20 else 'medium' if spam_score < 40 else 'high'
    
    return jsonify({
        'spam_score': min(spam_score, 100),
        'spam_level': spam_level,
        'warnings': warnings,
        'safe_to_post': spam_score < 40
    })

@app.route('/api/subreddit-rules/<subreddit>', methods=['GET'])
def get_subreddit_rules(subreddit):
    """Get subreddit rules (simplified - expand with actual API calls)"""
    # Hardcoded common rules - you can expand this with actual Reddit API calls
    rules = {
        'wallstreetbets': {
            'self_promo': 'restricted',
            'links': 'not_allowed',
            'warnings': ['No self-promotion', 'No external links in comments']
        },
        'algotrading': {
            'self_promo': 'allowed_with_disclosure',
            'links': 'allowed',
            'warnings': ['Include disclosure if mentioning your product']
        },
        'stocks': {
            'self_promo': 'restricted',
            'links': 'allowed',
            'warnings': ['Self-promotion requires mod approval']
        }
    }
    
    subreddit_clean = subreddit.replace('r/', '').lower()
    subreddit_rules = rules.get(subreddit_clean, {
        'self_promo': 'unknown',
        'links': 'unknown',
        'warnings': ['Check subreddit rules before posting']
    })
    
    return jsonify(subreddit_rules)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False') == 'True')