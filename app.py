"""
Flask Web Application for Reddit Lead Finder
"""

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from main import RedditLeadFinder
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Global variable for lead finder instance
lead_finder = None

def get_anthropic_client():
    """Initialize Anthropic client lazily only when needed."""
    try:
        from anthropic import Anthropic
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not set")
            return None
        print("Anthropic client initialized successfully")
        return Anthropic(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize Anthropic client: {e}")
        return None

def get_lead_finder():
    """Get or create RedditLeadFinder instance."""
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
    """Health check endpoint for Railway."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/scan', methods=['POST'])
def scan_reddit():
    """Scan Reddit for leads."""
    try:
        data = request.json
        keywords = data.get('keywords', [])
        date_range = data.get('date_range', 7)
        search_comments = data.get('search_comments', True)
        
        print(f"Scanning with {len(keywords)} keywords")
        
        finder = get_lead_finder()
        
        # Use custom keywords if provided, otherwise use defaults
        results = finder.search_reddit(
            keywords=keywords if keywords else None,
            date_range_days=date_range,
            limit=50,
            search_comments=search_comments
        )
        
        print(f"Found {len(results)} results")
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
    
    except Exception as e:
        print(f"Error in scan_reddit: {e}")
        import traceback
        traceback.print_exc()
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
        reply_mode = data.get('reply_mode', 'full')  # ghost, soft, full
        reply_length = data.get('reply_length', 'medium')  # short, medium, long
        post_type = data.get('type', 'post')
        
        print(f"\n=== Generate Reply Request ===")
        print(f"Post type: {post_type}")
        print(f"Context preview: {context[:200]}...")
        print(f"Intent: {intent_label}")
        print(f"Reply mode: {reply_mode}")
        print(f"Reply length: {reply_length}")
        
        if not context:
            return jsonify({
                'success': False,
                'error': 'No context provided'
            }), 400
        
        # Try to get Anthropic client
        client = get_anthropic_client()
        
        if not client:
            print("⚠️ Anthropic client not available, using template fallback")
            reply = generate_template_reply(context, intent_label, reply_mode, reply_length)
            return jsonify({
                'success': True,
                'reply': reply,
                'method': 'template',
                'warning': 'AI generation unavailable - check ANTHROPIC_API_KEY'
            })
        
        # Generate length-specific instructions
        length_instructions = {
            'short': "Keep it VERY short - just 1-2 sentences maximum, be extremely concise",
            'medium': "Keep it 4-6 sentences total - provide detailed advice",
            'long': "Keep it 7+ sentences total - give comprehensive guidance"
        }
        
        # Generate AI reply using Claude based on reply mode
        if reply_mode == 'ghost':
            prompt = f"""You are a helpful trader engaging in a Reddit discussion. Your goal is to provide pure value without any brand mentions.

Here's a Reddit {post_type} you're replying to:
---
{context}
---

Intent/Topic: {intent_label}

Write a natural, helpful reply that:
1. Directly addresses their specific question or concern from the post above
2. Provides concrete, actionable tips based on their exact situation
3. Sounds like a real human trader sharing experience (casual, conversational tone)
4. NO brand mentions or tool recommendations - pure educational value only
5. {length_instructions[reply_length]}
6. NO generic advice - everything must be relevant to their specific post content
7. IMPORTANT: Use regular dashes (-) not em dashes (—)

Make it sound natural and helpful, not salesy or corporate. Write like you're genuinely trying to help a fellow trader."""
        
        elif reply_mode == 'soft':
            prompt = f"""You are a helpful trader engaging in a Reddit discussion. Your goal is to provide genuine value while naturally mentioning TradingWizard AI (without links).

TradingWizard AI is a platform that:
- Provides AI-powered chart analysis for any stock, crypto, or forex symbol
- Users can select any symbol and get instant technical analysis
- Offers automated chart reading and pattern recognition
- Helps traders make data-driven decisions

Here's a Reddit {post_type} you're replying to:
---
{context}
---

Intent/Topic: {intent_label}

Write a natural, helpful reply that:
1. Directly addresses their specific question or concern from the post above
2. Provides concrete, actionable tips based on their exact situation
3. Sounds like a real human trader sharing experience (casual, conversational tone)
4. Naturally mentions TradingWizard AI as a helpful tool (1 sentence max, weave it in naturally) - NO LINKS
5. {length_instructions[reply_length]}
6. NO generic advice - everything must be relevant to their specific post content
7. IMPORTANT: Use regular dashes (-) not em dashes (—)

Make it sound natural and helpful, not salesy or corporate. Write like you're genuinely trying to help a fellow trader."""
        
        else:  # full mode
            prompt = f"""You are a helpful trader engaging in a Reddit discussion. Your goal is to provide genuine value while naturally mentioning TradingWizard.ai with a link when relevant.

TradingWizard.ai is a platform that:
- Provides AI-powered chart analysis for any stock, crypto, or forex symbol (not just uploads!)
- Users can select any symbol and get instant technical analysis
- Offers automated chart reading and pattern recognition
- Helps traders make data-driven decisions

Here's a Reddit {post_type} you're replying to:
---
{context}
---

Intent/Topic: {intent_label}

Write a natural, helpful reply that:
1. Directly addresses their specific question or concern from the post above
2. Provides concrete, actionable tips based on their exact situation
3. Sounds like a real human trader sharing experience (casual, conversational tone)
4. Naturally mentions TradingWizard.ai as a helpful tool with a link (1 sentence max, weave it in naturally)
5. Includes a casual disclosure like '(full disclosure: I work on it)' or '(I help build it)'
6. {length_instructions[reply_length]}
7. NO generic advice - everything must be relevant to their specific post content
8. IMPORTANT: Use regular dashes (-) not em dashes (—)

Make it sound natural and helpful, not salesy or corporate. Write like you're genuinely trying to help a fellow trader."""

        try:
            print(f"🚀 Sending request to Anthropic API...")
            print(f"📊 API Key present: {bool(os.getenv('ANTHROPIC_API_KEY'))}")
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            reply = message.content[0].text
            print(f"✅ Got AI reply: {reply[:150]}...")
            
            return jsonify({
                'success': True,
                'reply': reply,
                'method': 'ai'
            })
            
        except Exception as ai_error:
            print(f"❌ AI generation failed: {ai_error}")
            print(f"❌ Error type: {type(ai_error).__name__}")
            print(f"❌ Full error: {str(ai_error)}")
            reply = generate_template_reply(context, intent_label, reply_mode, reply_length)
            return jsonify({
                'success': True,
                'reply': reply,
                'method': 'template_fallback',
                'error': str(ai_error)
            })
    
    except Exception as e:
        print(f"❌ Error in generate_reply: {e}")
        import traceback
        traceback.print_exc()
        
        reply = generate_template_reply(
            data.get('context', ''),
            data.get('intent_label', 'General discussion'),
            data.get('reply_mode', 'full')
        )
        return jsonify({
            'success': True,
            'reply': reply,
            'method': 'template_fallback',
            'error': str(e)
        })

def generate_template_reply(context: str, intent_label: str, reply_mode: str, reply_length: str) -> str:
    """Generate a template-based reply as fallback."""
    tips = {
        'Tool-seeking': "Start by defining your timeframe and setup type. Map key support/resistance levels, then confirm with momentum indicators. Focus on keeping your edge simple and repeatable.",
        'How-to': "Break it into steps: define what you're analyzing, overlay key levels, add 1-2 confirmation indicators, and document your rules. Simple beats complex every time.",
        'Problem-solving': "Common issue: too many conflicting indicators. Strip it down to price action, volume, and one momentum indicator. Also check if you're trading during choppy hours.",
        'General discussion': "For consistent results, document your setups, track your stats, and refine what's actually profitable vs what just feels good."
    }
    
    tip = tips.get(intent_label, tips['General discussion'])
    
    # Adjust tip length based on reply_length
    if reply_length == 'short':
        # Make it extremely short - just key words/phrases
        short_tips = {
            'Tool-seeking': "Focus on price action and volume.",
            'How-to': "Keep it simple - price, levels, momentum.",
            'Problem-solving': "Strip down to basics - price action only.",
            'General discussion': "Document everything, track stats."
        }
        tip = short_tips.get(intent_label, "Keep it simple and track your results.")
    elif reply_length == 'long':
        tip += " Remember to backtest your strategy and keep detailed logs of your trades for continuous improvement."
    
    if reply_mode == 'ghost':
        cta = " Tools that automate chart reading and setup identification can speed this up significantly."
    elif reply_mode == 'soft':
        cta = " TradingWizard AI can help automate chart analysis and pattern recognition for any symbol you're interested in."
    else:  # full mode
        cta = " If you want AI-powered analysis for any chart, TradingWizard.ai lets you analyze stocks, crypto, or forex by just selecting the symbol - instant technical breakdown. (Disclosure: I help build it)"
    
    return tip + cta

@app.route('/api/filter-results', methods=['POST'])
def filter_results():
    """Filter and sort results based on user criteria."""
    try:
        data = request.json
        results = data.get('results', [])
        min_score = data.get('min_score', 0)
        max_score = data.get('max_score', 100)
        intent_filter = data.get('intent_filter', '')
        sort_by = data.get('sort_by', 'score')
        
        print(f"\n=== Filter Results Request ===")
        print(f"Results count: {len(results)}")
        print(f"Score range: {min_score}-{max_score}")
        print(f"Intent filter: {intent_filter}")
        print(f"Sort by: {sort_by}")
        
        # Filter by score range
        filtered_results = [
            r for r in results 
            if min_score <= (r.get('score', 0)) <= max_score
        ]
        
        # Filter by intent if specified
        if intent_filter:
            filtered_results = [
                r for r in filtered_results 
                if r.get('intent_label', '') == intent_filter
            ]
        
        # Sort results
        if sort_by == 'score':
            filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        elif sort_by == 'date':
            filtered_results.sort(key=lambda x: x.get('created_utc', 0), reverse=True)
        elif sort_by == 'date-old':
            filtered_results.sort(key=lambda x: x.get('created_utc', 0))
        
        print(f"Filtered results count: {len(filtered_results)}")
        
        return jsonify({
            'success': True,
            'count': len(filtered_results),
            'results': filtered_results
        })
    
    except Exception as e:
        print(f"Error in filter_results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/default-keywords', methods=['GET'])
def get_default_keywords():
    """Get default keywords."""
    finder = get_lead_finder()
    return jsonify({
        'keywords': finder.config.get('keywords_core', [])
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)