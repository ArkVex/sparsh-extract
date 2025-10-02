# app.py
import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from llama_extract_service import llama_service

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/extract', methods=['POST'])
def extract():
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is PDF
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Please upload a PDF file'}), 400
        
        # Extract using LlamaExtract service
        result = llama_service.extract_from_buffer(file.stream, file.filename)
        
        if result['success']:
            return jsonify({
                'message': 'Clinical protocol extraction successful',
                'filename': result['filename'],
                'extracted_data': result['data'],
                'schema_type': result['schema_type'],
                'agent_name': result['agent_name']
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)