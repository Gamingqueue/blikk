from flask import Flask, request, jsonify, render_template
import json
import os
from email_reader import get_latest_netflix_code

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Load keys from file
with open('keys.json') as f:
    VALID_KEYS = set(json.load(f))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-code', methods=['POST'])
def get_code():
    data = request.json
    user_key = data.get('key')
    
    if not user_key:
        return jsonify({'error': 'Key is required'}), 400
        
    if user_key not in VALID_KEYS:
        return jsonify({'error': 'Invalid key provided'}), 403
        
    code = get_latest_netflix_code()
    if code:
        return jsonify({'code': code, 'success': True})
    else:
        return jsonify({'error': 'No recent Netflix code found'}), 404

@app.route('/validate-key', methods=['POST'])
def validate_key():
    """Real-time key validation endpoint"""
    data = request.json
    user_key = data.get('key')
    
    if not user_key:
        return jsonify({'valid': False, 'message': 'Key is required'})
        
    if user_key in VALID_KEYS:
        return jsonify({'valid': True, 'message': 'Valid key'})
    else:
        return jsonify({'valid': False, 'message': 'Invalid key'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
