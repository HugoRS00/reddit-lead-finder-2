"""
Flask Web Application for Reddit Lead Finder
"""

from flask import Flask, render_template, jsonify, request
from main import RedditLeadFinder
import json
import os
from anthropic import Anthropic

app = Flask(__name__)

# Initialize clients
lead_finder = None
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY', ''))

def get_lead_finder():
    global lead_finder
    if lead_finder is None:
        lead_finder = RedditLeadFinder()
    return lead_finder

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/api/scan', methods=['POST'])
def scan_reddit():
    """Scan Reddit for leads."""
    try:
        data = request.json
        keywords = data.get('keywords', [])
        date_range = data.get('date_range', 7)
        search_comments = data.get('search_comments', True)
        
        finder = get_lead_finder()
        
        # Use custom keywords if provided, otherwise use defaults
        results = finder.search_reddit(
            keywords=keywords if keywords else None,
            date_range_days=date_range,
            limit=50,
            search_comments=search_comments
        )
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-reply', methods=['POST'])
def generate_reply():
    """Generate AI reply for a specific lead."""
    try:
        data = request.json
        context = data.get('context', '')
        intent_label = data.get('intent_label', 'General discussion')
        include_link = data.get('include_link', True)
        post_type = data.get('type', 'post')
        
        if not context:
            return jsonify({
                'success': False,
                'error': 'No context provided'
            }), 400
        
        # Check if Anthropic API key is set
        if not os.getenv('ANTHROPIC_API_KEY'):
            # Fallback to template-based reply
            reply = generate_template_reply(context, intent_label, include_link)
            return jsonify({
                'success': True,
                'reply': reply,
                'method': 'template'
            })
        
        # Generate AI reply using Claude
        prompt = f"""You are helping with outbound marketing for TradingWizard.ai, a platform that helps traders analyze charts and make better trading decisions.

TradingWizard.ai features:
- AI-powered chart analysis for any stock, crypto, or forex symbol (not just chart uploads)
- Select any symbol and get instant AI analysis
- Technical analysis automation
- Trading signals and market scans
- Backtesting capabilities

Context from Reddit {post_type}:
\"\"\"{context}\"\"\"

Intent: {intent_label}

Generate a helpful, natural reply that:
1. First provides 50% genuine value (concrete trading tips, actionable advice, mini checklist)
2. Then 50% soft mention of TradingWizard.ai
3. Sounds conversational and human, not salesy
4. Is 3-5 sentences total
5. {"Includes a natural mention of TradingWizard.ai with a soft CTA" if include_link else "Mentions helpful tools generally without specific brands"}
6. {"Include a light disclosure like '(I work on TradingWizard.ai)' at the end" if include_link else "No disclosure needed"}

Keep it natural, helpful, and not spammy. Focus on being genuinely useful first."""

        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        reply = message.content[0].text
        
        return jsonify({
            'success': True,
            'reply': reply,
            'method': 'ai'
        })
    
    except Exception as e:
        print(f"Error generating AI reply: {e}")
        # Fallback to template
        reply = generate_template_reply(
            data.get('context', ''),
            data.get('intent_label', 'General discussion'),
            data.get('include_link', True)
        )
        return jsonify({
            'success': True,
            'reply': reply,
            'method': 'template_fallback'
        })

def generate_template_reply(context: str, intent_label: str, include_link: bool) -> str:
    """Generate a template-based reply as fallback."""
    tips = {
        'Tool-seeking': "Start by defining your timeframe and setup type. Map key support/resistance levels, then confirm with momentum indicators. Focus on keeping your edge simple and repeatable.",
        'How-to': "Break it into steps: define what you're analyzing, overlay key levels, add 1-2 confirmation indicators, and document your rules. Simple beats complex every time.",
        'Problem-solving': "Common issue: too many conflicting indicators. Strip it down to price action, volume, and one momentum indicator. Also check if you're trading during choppy hours.",
        'General discussion': "For consistent results, document your setups, track your stats, and refine what's actually profitable vs what just feels good."
    }
    
    tip = tips.get(intent_label, tips['General discussion'])
    
    if include_link:
        cta = " If you want AI-powered analysis for any chart, TradingWizard.ai lets you analyze stocks, crypto, or forex by just selecting the symbol—instant technical breakdown. (Disclosure: I help build it)"
    else:
        cta = " Tools that automate chart reading and setup identification can speed this up significantly."
    
    return tip + cta

@app.route('/api/default-keywords', methods=['GET'])
def get_default_keywords():
    """Get default keywords."""
    finder = get_lead_finder()
    return jsonify({
        'keywords': finder.config.get('keywords_core', [])
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
