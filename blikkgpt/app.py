
from flask import Flask, request, jsonify, render_template
import json
import os
from email_reader import get_latest_chatgpt_code

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

    code = get_latest_chatgpt_code()
    if code:
        return jsonify({'code': code, 'success': True})
    else:
        return jsonify({'error': 'No recent ChatGPT code found'}), 404

@app.route('/validate-key', methods=['POST'])
def validate_key():
    data = request.json
    user_key = data.get("key")
    is_valid = user_key in VALID_KEYS
    return jsonify({'valid': is_valid})
