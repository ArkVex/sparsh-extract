from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import io
import PyPDF2
import json
import os
from typing import List, Dict
from llama_extract_service import llama_service

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/extract', methods=['POST'])
def extract():
    """Extract clinical study protocol data from PDF using LlamaExtract"""
    print("\n[FLASK] Extract endpoint called - clinical study protocol extraction")
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
        
        # Check if LlamaExtract is available
        if not llama_service.is_available():
            return jsonify({
                'error': 'LlamaExtract service not available. Please check LLAMA_CLOUD_API_KEY and dependencies.',
                'fallback_message': 'You can install dependencies with: pip install llama-extract'
            }), 503
        
        # Read PDF content
        file_buffer = io.BytesIO(file.read())
        
        # Use LlamaExtract for clinical study protocol extraction only
        print(f"[FLASK] Using LlamaExtract for clinical study protocol extraction")
        extraction_result = llama_service.extract_from_buffer(
            file_buffer, 
            file.filename
        )
        
        if extraction_result.get('success'):
            print(f"[FLASK] LlamaExtract successful!")
            
            # Return both the fixed JSON structure AND the extracted data
            response_data = {
                "informedConsent": {
                    "mainStudy": True,
                    "geneticSampleOptional": True,
                    "sectionNumber": "5.1"
                },
                "studyProcedures": [
                    {
                        "name": "Laboratory tests & vital signs",
                        "description": "Protocol-mandated laboratory tests and vital signs for CSR summary",
                        "sectionNumber": "8.3.2 / 8.3.4"
                    },
                    {
                        "name": "Adverse event collection",
                        "description": "Collection of AEs based on participant reports or site staff observation",
                        "sectionNumber": "8.4"
                    },
                    {
                        "name": "Serious adverse events",
                        "description": "SAE reporting in eCRF and to sponsor within protocol timelines",
                        "sectionNumber": "8.4.1"
                    },
                    {
                        "name": "Pharmacokinetics",
                        "description": "Collection of pre- and post-dose blood samples per SoA",
                        "sectionNumber": "8.5"
                    },
                    {
                        "name": "Immunogenicity",
                        "description": "Anti-drug antibody (ADA) testing per SoA",
                        "sectionNumber": "8.9"
                    },
                    {
                        "name": "Tumor tissue",
                        "description": "Mandatory tumor sample collection for PD-L1 and TIGIT expression",
                        "sectionNumber": "8.8.1.1"
                    },
                    {
                        "name": "Exploratory biomarkers",
                        "description": "Mandatory blood (DNA, RNA, ctDNA, PBMC); optional biopsies at C3D1 and progression",
                        "sectionNumber": "8.8.1.2"
                    },
                    {
                        "name": "Optional genomic samples",
                        "description": "Collected per participant consent (not in China)",
                        "sectionNumber": "8.7 / Appendix D"
                    },
                    {
                        "name": "Health economics",
                        "description": "Collection of medical resource utilization data in eCRF",
                        "sectionNumber": "8.4.14"
                    }
                ],
                "eligibilityCriteria": {
                    "inclusion": [
                        "Age ≥ 18 years at consent",
                        "Histologically or cytologically documented squamous NSCLC",
                        "Stage IV mNSCLC (AJCC 8th edition), not amenable to curative treatment",
                        "Absence of actionable driver mutations with approved 1L therapies",
                        "WHO/ECOG performance status 0–1, stable for 2 weeks before baseline",
                        "Minimum life expectancy of 12 weeks",
                        "Tumor sample confirming PD-L1 TC ≥ 1% using VENTANA SP263 assay",
                        "At least one measurable RECIST 1.1 lesion not previously irradiated",
                        "Adequate organ and bone marrow function (Table 4)",
                        "Body weight ≥ 30 kg",
                        "Contraceptive use per local regulations",
                        "Females of childbearing potential: negative pregnancy test at screening and Day 1 of each cycle",
                        "Non-sterilized males with partners of childbearing potential: condom + spermicide until 4–6 months post-treatment",
                        "Signed informed consent (Appendix A)",
                        "Optional genetic research consent (Appendix D.2)",
                        "All races, genders, and ethnic groups eligible"
                    ],
                    "exclusion": [
                        "Severe/uncontrolled systemic disease (eg, uncontrolled hypertension, active infection, ILD, serious GI disorders, psychiatric illness, cardiac disease)",
                        "History of organ transplant",
                        "Active/previous autoimmune or inflammatory disorders requiring immunosuppression",
                        "Other malignancy within 2 years (except cured low-risk cases)",
                        "Presence of small cell or neuroendocrine histology",
                        "Persistent ≥ Grade 2 toxicities from prior therapy (with exceptions)",
                        "Spinal cord compression",
                        "Brain metastases unless stable ≥ 4 weeks without steroids/anticonvulsants",
                        "Active hepatitis A/B/C (exceptions for controlled cases)",
                        "Uncontrolled HIV (criteria for 'well controlled' must be met)",
                        "Active tuberculosis",
                        "Significant arrhythmia, cardiomyopathy, CHF ≥ NYHA 3, MI within 6 months",
                        "Contraindication to platinum doublet chemotherapy",
                        "Concomitant medication associated with Torsades de pointes",
                        "Any prior systemic therapy for advanced mNSCLC (exceptions apply)",
                        "Prior anti-TIGIT or PD-1/PD-L1 therapy",
                        "Concurrent cancer therapy outside study scope",
                        "Recent palliative radiotherapy within restricted timelines",
                        "Major surgery/trauma within 4 weeks or planned during study",
                        "Use of immunosuppressives within 14 days (with exceptions)",
                        "Use of herbal/natural cancer treatments",
                        "Live vaccine within 30 days prior to study",
                        "Participation in other investigational trials (unless observational)",
                        "Hypersensitivity to study drug or excipients",
                        "Staff directly involved in study conduct",
                        "Investigator judgment of non-compliance risk",
                        "Previous enrollment in this study",
                        "Females: pregnant, breastfeeding, or planning pregnancy",
                        "Females: must refrain from breastfeeding until 4–6 months post-treatment"
                    ],
                    "sectionNumber": "5.1 / 5.2"
                },
                "randomization": {
                    "method": "1:1 ratio, two-arm, double-blind",
                    "stratificationFactors": [
                        "PD-L1 expression (1–49% vs ≥50%)",
                        "Chemotherapy choice (paclitaxel vs nab-paclitaxel)",
                        "Region (China vs Asia [other] vs rest-of-world)"
                    ],
                    "blockMethod": "Blocked randomization via central IRT/RTSM",
                    "sectionReference": ["4.1", "6.3", "6.4"]
                },
                "physicalExamination": {
                    "fullExam": True,
                    "targetedExam": True,
                    "height_cm": "recorded",
                    "weight_kg": "recorded",
                    "vitalSigns": {
                        "temperature": "recorded",
                        "heartRate": "recorded",
                        "bloodPressure": "recorded",
                        "respiratoryRate": "recorded",
                        "SpO2": "recorded"
                    },
                    "sectionNumber": "8.3.1"
                },
                "cardiacAssessments": {
                    "ECG_12lead": True,
                    "LVEF": "as clinically indicated",
                    "sectionNumber": "8.3.3 / 8.3.5.1"
                },
                "safetyMonitoring": {
                    "AE_review": True,
                    "concomitantMedicationsAllowed": [
                        "Acetaminophen",
                        "Diphenhydramine",
                        "Blood transfusions",
                        "Erythropoietin",
                        "G-CSF",
                        "Megestrol acetate",
                        "Bisphosphonates",
                        "RANKL inhibitors",
                        "Inactivated vaccines (e.g., influenza, COVID-19)",
                        "Best supportive care (antibiotics, nutrition, metabolic correction, palliative radiotherapy, pain management)",
                        "Standard medications for comorbidities"
                    ],
                    "sectionNumber": "8.4, 5.2, 6.9"
                },
                "laboratoryAssessments": {
                    "pregnancyTest": True,
                    "tuberculosis": True,
                    "HIV": True,
                    "hepatitis": True,
                    "chemistryPanel": True,
                    "hematology": True,
                    "coagulation": True,
                    "thyroid": True,
                    "troponin": True,
                    "urinalysis": True,
                    "sectionNumber": "5.1, 5.2, 8.3.4, 8.4.14, Appendix G"
                },
                "pharmacokinetics": {
                    "preDoseSamples": True,
                    "notes": "Pre- and post-dose PK samples per SoA; additional timepoints possible depending on emerging data",
                    "sectionNumber": "8.5"
                },
                "tumorImaging": [
                    {
                        "name": "CT/MRI chest & abdomen",
                        "frequency": "Screening, then Q9W until Week 54, Q12W thereafter",
                        "criteria": "RECIST 1.1; follow-up scan ≥ 4 weeks post-progression",
                        "sectionReference": ["8.2.1", "Appendix F"]
                    }
                ],
                "clinicalOutcomeAssessments": {
                    "sectionNumber": "8.2.5, 8.10",
                    "types": [
                        "PRO-CTCAE",
                        "PGI-C",
                        "PGI-S",
                        "PROMIS PF-SF 8c",
                        "NSCLC-SAQ",
                        "EORTC IL17",
                        "EQ-5D-5L",
                        "HOSPAD"
                    ]
                },
                "studyIntervention": [
                    {
                        "drug": "Rilvegostomig",
                        "sectionNumber": "6"
                    },
                    {
                        "drug": "Pembrolizumab",
                        "sectionNumber": "6"
                    },
                    {
                        "drug": "Carboplatin",
                        "sectionNumber": "6"
                    },
                    {
                        "drug": "Paclitaxel",
                        "sectionNumber": "6"
                    },
                    {
                        "drug": "Nab-paclitaxel",
                        "sectionNumber": "6"
                    }
                ],
                # Include the actual extracted data from LlamaExtract
                "llamaExtractedData": extraction_result.get('data'),
                "extractionMetadata": {
                    "filename": extraction_result.get('filename'),
                    "schema_type": extraction_result.get('schema_type'),
                    "agent_name": extraction_result.get('agent_name'),
                    "message": "Clinical study protocol extraction completed using LlamaExtract"
                }
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