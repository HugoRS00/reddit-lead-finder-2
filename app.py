"""
Flask Web Application for Reddit Lead Finder
"""

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import os
from services.reddit_service import RedditLeadFinder
from services.x_service import XLeadFinder
from services.ai_service import AIService

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Global instances
reddit_finder = None
x_finder = None
ai_service = None
x_finder_error = None

def get_reddit_finder():
    global reddit_finder
    if reddit_finder is None:
        reddit_finder = RedditLeadFinder()
    return reddit_finder

def get_x_finder():
    global x_finder, x_finder_error
    if x_finder is None:
        try:
            x_finder = XLeadFinder()
            x_finder_error = None
        except Exception as e:
            x_finder_error = str(e)
            print(f"Warning: X lead finder unavailable - {e}")
            return None
    return x_finder

def get_ai_service():
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service

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
        date_range = int(data.get('date_range', 7))
        search_comments = data.get('search_comments', True)
        platforms = data.get('platforms') or ['reddit']
        min_followers = int(data.get('min_followers', 0))
        min_engagement = int(data.get('min_engagement', 0))
        
        print(f"Scanning with {len(keywords)} keywords across platforms: {platforms}")
        
        combined_results = []
        errors = {}
        rate_limits = {}
        
        # Reddit Scan
        if 'reddit' in platforms:
            try:
                finder = get_reddit_finder()
                results = finder.search_reddit(
                    keywords=keywords if keywords else None,
                    date_range_days=date_range,
                    limit=50,
                    search_comments=search_comments
                )
                combined_results.extend(results)
                print(f"Found {len(results)} Reddit results")
            except Exception as e:
                errors['reddit'] = str(e)
                print(f"Error scanning Reddit: {e}")

        # X Scan
        if 'x' in platforms:
            try:
                finder = get_x_finder()
                if finder:
                    results = finder.search_x(
                        keywords=keywords if keywords else None,
                        date_range_days=date_range,
                        limit=50,
                        min_followers=min_followers,
                        min_engagement=min_engagement
                    )
                    combined_results.extend(results)
                    print(f"Found {len(results)} X results")
                    if finder.rate_snapshot:
                        rate_limits['x'] = finder.rate_snapshot
                else:
                    errors['x'] = x_finder_error or "X configuration missing"
            except Exception as e:
                errors['x'] = str(e)
                print(f"Error scanning X: {e}")

        # Sort and limit
        combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(combined_results),
            'results': combined_results,
            'rate_limits': rate_limits,
            'errors': errors
        })
    
    except Exception as e:
        print(f"Error in scan_leads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-reply', methods=['POST'])
def generate_reply():
    """Generate AI reply for a specific lead."""
    try:
        data = request.json
        context = data.get('context', '')
        intent_label = data.get('intent_label', 'General discussion')
        reply_mode = data.get('reply_mode', 'full')
        reply_length = data.get('reply_length', 'medium')
        voice_profile = data.get('voice_profile')
        
        if not context:
            return jsonify({'success': False, 'error': 'No context provided'}), 400
            
        service = get_ai_service()
        result = service.generate_reply(
            context, intent_label, reply_mode, reply_length, voice_profile
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in generate_reply: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/default-keywords', methods=['GET'])
def get_default_keywords():
    """Get default keywords."""
    finder = get_reddit_finder()
    return jsonify({
        'keywords': finder.config.get('keywords_core', [])
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
