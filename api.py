#!/usr/bin/env python3
"""
Web API wrapper for Reddit Lead Finder
Allows deployment on platforms like Railway
"""

from flask import Flask, jsonify, request
import os
import json
from main import RedditLeadFinder
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'Reddit Lead Finder API for TradingWizard.ai',
        'version': '1.0',
        'endpoints': {
            '/': 'This page',
            '/health': 'Health check',
            '/scan': 'Trigger a new scan (POST)',
            '/latest': 'Get latest results (GET)'
        }
    })

@app.route('/health')
def health():
    """Health check for Railway"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/scan', methods=['POST'])
def trigger_scan():
    """Trigger a new Reddit scan"""
    try:
        # Get optional parameters from request
        data = request.get_json() or {}
        days = data.get('days', 7)
        limit = data.get('limit', 25)
        
        # Run the scan
        finder = RedditLeadFinder()
        results = finder.search_reddit(date_range_days=days, limit=limit)
        
        # Save results
        output_file = 'leads.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'found': len(results),
            'message': f'Found {len(results)} opportunities',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/latest', methods=['GET'])
def get_latest():
    """Get the latest scan results"""
    try:
        if os.path.exists('leads.json'):
            with open('leads.json', 'r') as f:
                results = json.load(f)
            return jsonify({
                'status': 'success',
                'count': len(results),
                'results': results
            })
        else:
            return jsonify({
                'status': 'no_data',
                'message': 'No scan results yet. Trigger a scan first.'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)