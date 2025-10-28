"""
Flask Web Application for Reddit Lead Finder
"""

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from main import RedditLeadFinder, XLeadFinder
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Global variable for lead finder instance
lead_finder = None
x_lead_finder = None
x_lead_finder_error = None

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

def get_x_lead_finder():
    """Get or create XLeadFinder instance."""
    global x_lead_finder, x_lead_finder_error
    if x_lead_finder is None:
        try:
            x_lead_finder = XLeadFinder()
            x_lead_finder_error = None
        except Exception as exc:
            x_lead_finder_error = str(exc)
            print(f"Warning: X lead finder unavailable - {exc}")
            return None
    return x_lead_finder

@app.route('/') 
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Railway."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/scan', methods=['POST'])
def scan_leads():
    """Scan selected social platforms for leads."""
    try:
        data = request.json
        keywords = data.get('keywords', [])
        date_range = data.get('date_range', 7)
        search_comments = data.get('search_comments', True)
        platforms = data.get('platforms') or ['reddit']
        
        print(f"Scanning with {len(keywords)} keywords across platforms: {platforms}")
        
        finder = get_lead_finder()
        combined_results = []
        errors = {}
        max_results = finder.config.get('max_results', 50)
        
        # Use custom keywords if provided, otherwise use defaults
        custom_keywords = keywords if keywords else None

        if 'reddit' in platforms:
            try:
                reddit_results = finder.search_reddit(
                    keywords=custom_keywords,
                    date_range_days=date_range,
                    limit=max_results,
                    search_comments=search_comments
                )
                combined_results.extend(reddit_results)
                print(f"Found {len(reddit_results)} Reddit results")
            except Exception as reddit_error:
                errors['reddit'] = str(reddit_error)
                print(f"Error scanning Reddit: {reddit_error}")

        if 'x' in platforms:
            x_finder = get_x_lead_finder()
            if not x_finder:
                errors['x'] = x_lead_finder_error or 'X integration not configured'
                print(f"Skipping X scan: {errors['x']}")
            else:
                try:
                    x_results = x_finder.search_x(
                        keywords=custom_keywords,
                        date_range_days=date_range,
                        limit=max_results
                    )
                    combined_results.extend(x_results)
                    print(f"Found {len(x_results)} X results")
                except Exception as x_error:
                    errors['x'] = str(x_error)
                    print(f"Error scanning X: {x_error}")

        combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        combined_results = combined_results[:max_results]

        if not combined_results and errors:
            error_messages = '; '.join(f"{platform.upper()}: {message}" for platform, message in errors.items())
            return jsonify({
                'success': False,
                'error': error_messages,
                'errors': errors
            }), 200

        response = {
            'success': True,
            'count': len(combined_results),
            'results': combined_results
        }

        if errors:
            response['errors'] = errors
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Error in scan_leads: {e}")
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
            'short': "ULTRA SHORT - just 1 sentence, maximum 10-15 words. Be extremely concise.",
            'medium': "Keep it 4-6 sentences total - provide detailed advice with line breaks between sentences for readability",
            'long': "Keep it 7+ sentences total with line breaks for readability - give comprehensive guidance"
        }
        
        # Generate AI reply using Claude based on reply mode
        if reply_mode == 'ghost':
            prompt = f"""You're a real trader commenting on Reddit. Write like a human who's been trading for years and genuinely wants to help.

Here's what someone posted:
---
{context}
---

Topic: {intent_label}

Reply naturally - like you're texting a friend who asked for trading advice. Be conversational, use different sentence lengths, maybe throw in some trading slang or abbreviations. {length_instructions[reply_length]}

Key things:
- Answer their specific question directly
- Share real trading experience, not textbook stuff
- Use casual language (like "tbh", "imo", "fwiw" occasionally)
- Vary your sentence structure - some short, some longer
- NO brand mentions or tool recommendations
- Sound like you're actually helping, not selling anything

Write like a real person, not a bot."""
        
        elif reply_mode == 'soft':
            prompt = f"""You're a real trader commenting on Reddit. Write like a human who's been trading for years and genuinely wants to help.

Here's what someone posted:
---
{context}
---

Topic: {intent_label}

Reply naturally - like you're texting a friend who asked for trading advice. Be conversational, use different sentence lengths, maybe throw in some trading slang or abbreviations. {length_instructions[reply_length]}

Key things:
- Answer their specific question directly
- Share real trading experience, not textbook stuff
- Use casual language (like "tbh", "imo", "fwiw" occasionally)
- Vary your sentence structure - some short, some longer
- Naturally mention TradingWizard AI as a helpful tool (1 sentence max, weave it in naturally) - NO LINKS
- Sound like you're actually helping, not selling anything

Write like a real person, not a bot."""
        
        else:  # full mode
            prompt = f"""You're a real trader commenting on Reddit. Write like a human who's been trading for years and genuinely wants to help.

Here's what someone posted:
---
{context}
---

Topic: {intent_label}

Reply naturally - like you're texting a friend who asked for trading advice. Be conversational, use different sentence lengths, maybe throw in some trading slang or abbreviations. {length_instructions[reply_length]}

Key things:
- Answer their specific question directly
- Share real trading experience, not textbook stuff
- Use casual language (like "tbh", "imo", "fwiw" occasionally)
- Vary your sentence structure - some short, some longer
- Naturally mention TradingWizard.ai as a helpful tool with a link (1 sentence max, weave it in naturally)
- Include a casual disclosure like '(full disclosure: I work on it)' or '(I help build it)'
- Sound like you're actually helping, not selling anything

Write like a real person, not a bot."""

        try:
            print(f"🚀 Sending request to Anthropic API...")
            print(f"📊 API Key present: {bool(os.getenv('ANTHROPIC_API_KEY'))}")
            
            # Generate multiple variants (A/B/C)
            variants = []
            for i in range(3):
                variant_prompt = prompt + f"\n\nGenerate variant {chr(65+i)} - make it slightly different in tone/style but same core message."
                
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=400,
                    messages=[{
                        "role": "user",
                        "content": variant_prompt
                    }]
                )
                
                variant_reply = message.content[0].text
                # Add line breaks if 4+ sentences
                processed_reply = add_line_breaks_if_needed(variant_reply)
                variants.append({
                    'letter': chr(65+i),  # A, B, C
                    'reply': processed_reply
                })
                print(f"✅ Got variant {chr(65+i)}: {processed_reply[:100]}...")
            
            return jsonify({
                'success': True,
                'variants': variants,
                'method': 'ai'
            })
            
        except Exception as ai_error:
            print(f"❌ AI generation failed: {ai_error}")
            print(f"❌ Error type: {type(ai_error).__name__}")
            print(f"❌ Full error: {str(ai_error)}")
            
            # Generate template variants
            variants = []
            for i in range(3):
                variant_reply = generate_template_reply(context, intent_label, reply_mode, reply_length, variant=i)
                # Add line breaks if 4+ sentences
                processed_reply = add_line_breaks_if_needed(variant_reply)
                variants.append({
                    'letter': chr(65+i),  # A, B, C
                    'reply': processed_reply
                })
            
            return jsonify({
                'success': True,
                'variants': variants,
                'method': 'template_fallback',
                'error': str(ai_error)
            })
    
    except Exception as e:
        print(f"❌ Error in generate_reply: {e}")
        import traceback
        traceback.print_exc()
        
        # Generate template variants for final fallback
        variants = []
        for i in range(3):
            variant_reply = generate_template_reply(
                data.get('context', ''),
                data.get('intent_label', 'General discussion'),
                data.get('reply_mode', 'full'),
                data.get('reply_length', 'medium'),
                variant=i
            )
            # Add line breaks if 4+ sentences
            processed_reply = add_line_breaks_if_needed(variant_reply)
            variants.append({
                'letter': chr(65+i),  # A, B, C
                'reply': processed_reply
            })
        
        return jsonify({
            'success': True,
            'variants': variants,
            'method': 'template_fallback',
            'error': str(e)
        })

def add_line_breaks_if_needed(text: str) -> str:
    """Add line breaks between sentences if there are 4 or more sentences."""
    import re
    
    # Split by sentence endings (. ! ?) but keep the punctuation
    sentences = re.split(r'([.!?])\s+', text)
    
    # Reconstruct sentences with punctuation
    reconstructed_sentences = []
    for i in range(0, len(sentences), 2):
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]
            reconstructed_sentences.append(sentence.strip())
        elif sentences[i].strip():
            reconstructed_sentences.append(sentences[i].strip())
    
    # Filter out empty sentences
    sentences = [s for s in reconstructed_sentences if s.strip()]
    
    if len(sentences) >= 4:
        # Add line breaks between sentences
        return '\n\n'.join(sentences)
    return text

def generate_template_reply(context: str, intent_label: str, reply_mode: str, reply_length: str, variant: int = 0) -> str:
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
        # Make it ULTRA short - just a few words
        ultra_short_tips = {
            'Tool-seeking': "Price action + volume.",
            'How-to': "Price, levels, momentum.",
            'Problem-solving': "Price action only.",
            'General discussion': "Track everything."
        }
        tip = ultra_short_tips.get(intent_label, "Keep it simple.")
    elif reply_length == 'long':
        tip += "\n\nRemember to backtest your strategy and keep detailed logs of your trades for continuous improvement."
    
    # Add variant-specific modifications
    if variant == 1:  # Variant B
        tip = tip.replace("Start by", "First, I'd").replace("Break it", "Honestly, break it").replace("Common issue", "Yeah, common issue")
    elif variant == 2:  # Variant C
        tip = tip.replace("Start by", "IMO, start by").replace("Break it", "Tbh, break it").replace("Common issue", "Fwiw, common issue")
    
    if reply_length == 'short':
        # Ultra short CTAs
        if reply_mode == 'ghost':
            cta = " Use tools."
        elif reply_mode == 'soft':
            cta = " TradingWizard AI helps."
        else:  # full mode
            cta = " TradingWizard.ai for analysis. (I help build it)"
    else:
        # Regular CTAs
        if reply_mode == 'ghost':
            cta = " Tools that automate chart reading and setup identification can speed this up significantly."
        elif reply_mode == 'soft':
            cta = " TradingWizard AI can help automate chart analysis and pattern recognition for any symbol you're interested in."
        else:  # full mode
            cta = " If you want AI-powered analysis for any chart, TradingWizard.ai lets you analyze stocks, crypto, or forex by just selecting the symbol - instant technical breakdown. (Disclosure: I help build it)"
    
    return tip + cta

@app.route('/api/save-lead', methods=['POST'])
def save_lead():
    """Save a lead with status tracking."""
    try:
        data = request.json
        lead_id = data.get('lead_id')
        status = data.get('status', 'saved')  # new, saved, replied, skipped
        source = data.get('source', 'unknown')
        
        print(f"\n=== Save Lead Request ===")
        print(f"Lead ID: {lead_id}")
        print(f"Status: {status}")
        print(f"Source: {source}")
        
        # In a real app, you'd save this to a database
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': f'Lead marked as {status}',
            'lead_id': lead_id,
            'status': status
        })
    
    except Exception as e:
        print(f"Error in save_lead: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
