from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

base_url = 'http://34.27.89.183:5000'  
@app.route('/api/start', methods=['POST'])
def start_session():
    """Start a new shopping session with initial query"""
    try:
        response = requests.post(f'{base_url}/api/start', json=request.get_json())
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/answer', methods=['POST'])
def submit_answer():
    """Submit answer to a follow-up question"""
    try:
        response = requests.post(f'{base_url}/api/answer', json=request.get_json())
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/answer-all', methods=['POST'])
def submit_all_answers():
    """Submit all answers to follow-up questions at once"""
    try:
        response = requests.post(f'{base_url}/api/answer-all', json=request.get_json())
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<session_id>', methods=['GET'])
def get_session_status(session_id):
    """Check session status"""
    try:
        response = requests.get(f'{base_url}/api/status/{session_id}')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/youtuber-comments', methods=['POST'])
def get_youtuber_comments():
    """Generate youtuber-style comments"""
    try:
        response = requests.post(f'{base_url}/api/youtuber-comments', json=request.get_json(),timeout=180)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        response = requests.get(f'{base_url}/api/health')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000) 