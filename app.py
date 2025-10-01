from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import io
import PyPDF2
import json
import os
from typing import List, Dict
from llama_extract_service import get_schema, llama_service

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/extract', methods=['POST'])
def extract():
    """Extract clinical study data from PDF pages 51-111 using LlamaExtract"""
    print("\n[FLASK] Extract endpoint called - using LlamaExtract")
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        
        # Check if file is selected
        if not file or file.filename == '':
            return jsonify({'error': 'No file uploaded'}), 400
            
        # Check file type
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400
            
        # Check file size (16MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        if file_size > 16 * 1024 * 1024:
            return jsonify({'error': 'File too large. Maximum 16MB allowed'}), 400
        
        print(f"[FLASK] File: {file.filename}")
        
        # Get schema type from request (default to comprehensive_clinical_study)
        schema_type = request.form.get('schema_type', 'comprehensive_clinical_study')
        
        # Check if LlamaExtract is available
        if not llama_service.is_available():
            return jsonify({
                'error': 'LlamaExtract service not available. Please check LLAMA_CLOUD_API_KEY and dependencies.',
                'fallback_message': 'You can install dependencies with: pip install llama-extract'
            }), 503
        
        # Read PDF content
        file_buffer = io.BytesIO(file.read())
        
        # Use LlamaExtract for structured data extraction
        print(f"[FLASK] Using LlamaExtract with schema: {schema_type}")
        extraction_result = llama_service.extract_from_buffer(
            file_buffer, 
            file.filename, 
            schema_type
        )
        
        if extraction_result.get('success'):
            print(f"[FLASK] LlamaExtract successful!")
            response_data = {
                'success': True,
                'filename': extraction_result.get('filename'),
                'schema_type': extraction_result.get('schema_type'),
                'agent_name': extraction_result.get('agent_name'),
                'extracted_data': extraction_result.get('data'),
                'message': 'Clinical data extraction completed using LlamaExtract'
            }
            return jsonify(response_data)
        else:
            print(f"[FLASK] LlamaExtract failed: {extraction_result.get('error')}")
            return jsonify({'error': extraction_result.get('error')}), 500
            
    except Exception as e:
        print(f"[FLASK] Server error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/')
def home():
    return send_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)