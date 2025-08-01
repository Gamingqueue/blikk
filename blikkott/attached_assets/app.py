from flask import Flask, request, jsonify, render_template
import json
from email_reader import get_latest_netflix_code

app = Flask(__name__)

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
    if user_key not in VALID_KEYS:
        return jsonify({'error': 'Invalid key'}), 403
    code = get_latest_netflix_code()
    if code:
        return jsonify({'code': code})
    else:
        return jsonify({'error': 'No recent code found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
