import os
import io
from typing import Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    print("Warning: PyPDF2 not available. Install with: pip install PyPDF2")
    PYPDF2_AVAILABLE = False

try:
    from llama_cloud_services import LlamaExtract
    LLAMA_EXTRACT_AVAILABLE = True
except ImportError:
    print("Warning: llama-cloud-services not available. Install with: pip install llama-cloud-services")
    LLAMA_EXTRACT_AVAILABLE = False

load_dotenv()

# =============================================================================
# CLINICAL STUDY PROTOCOL SCHEMA (ONLY SCHEMA)
# =============================================================================

def get_clinical_study_protocol_schema():
    """
    Schema for clinical study protocol extraction.
    """
    from pydantic import BaseModel, Field
    from typing import Optional, List

    class Activity(BaseModel):
        category: str = Field(description="The grouping category for the procedure, e.g., 'Laboratory Assessments', 'Biomarker assessments'.")
        procedure_name: str = Field(description="The specific name of the procedure, e.g., 'Full physical examination', 'Hematology'.")
        visit_schedule: str = Field(description="When this procedure occurs, e.g., 'Screening Day -28 to -1', 'Cycle 1 Day 1', 'Every 12 weeks'.")
        notes: Optional[str] = Field(None, description="Any special conditions or notes for this procedure.")
        protocol_section: Optional[str] = Field(None, description="Protocol section reference, e.g., 'Section 8.3.1'.")

    class ClinicalStudyProtocol(BaseModel):
        protocol_title: str = Field(description="The official title of the study.")
        sponsor: str = Field(description="The sponsoring organization name.")
        protocol_version: str = Field(description="The protocol document version.")
        intervention_activities: List[Activity] = Field(description="Procedures and assessments during the intervention period.")
        post_intervention_activities: List[Activity] = Field(description="Procedures and assessments during post-intervention follow-up.")
        footnotes: Optional[str] = Field(None, description="Important footnotes from the schedule of activities.")
        abbreviations: Optional[str] = Field(None, description="Key abbreviations and their definitions.")

    return ClinicalStudyProtocol


# =============================================================================
# SERVICE CLASS
# =============================================================================

class LlamaExtractService:
    """
    LlamaExtract service for clinical study protocol extraction from PDFs.
    """
    def __init__(self):
        self.api_key = os.getenv('LLAMA_CLOUD_API_KEY')
        self.extractor = None
        if self.api_key and LLAMA_EXTRACT_AVAILABLE:
            try:
                # Initialize client (API key is automatically loaded from environment)
                self.extractor = LlamaExtract()
                print(f"[LlamaExtract] Initialized successfully")
            except Exception as e:
                print(f"[LlamaExtract] Failed to initialize: {e}")
                self.extractor = None
        elif not self.api_key:
            print("[LlamaExtract] No LLAMA_CLOUD_API_KEY found in environment")
        else:
            print("[LlamaExtract] llama-cloud-services package not available")
    
    def extract_pages_20_to_40(self, input_path, output_path):
        """Extract pages 20-40 from PDF and save to new file"""
        if not PYPDF2_AVAILABLE:
            print("[LlamaExtract] PyPDF2 not available, processing entire PDF")
            return input_path
            
        try:
            with open(input_path, 'rb') as input_file:
                reader = PyPDF2.PdfReader(input_file)
                writer = PyPDF2.PdfWriter()
                
                total_pages = len(reader.pages)
                print(f"[LlamaExtract] Total pages in PDF: {total_pages}")
                
                # Extract pages 20-40 (0-indexed, so 19-39)
                start_page = 19  # Page 20 (0-indexed)
                end_page = min(39, total_pages - 1)  # Page 40 or last page
                
                if start_page >= total_pages:
                    print(f"[LlamaExtract] Warning: Start page 20 exceeds total pages ({total_pages})")
                    return input_path
                
                print(f"[LlamaExtract] Extracting pages 20-{end_page + 1} (total: {end_page - start_page + 1} pages)")
                
                for page_num in range(start_page, end_page + 1):
                    writer.add_page(reader.pages[page_num])
                
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                return output_path
                
        except Exception as e:
            print(f"[LlamaExtract] Error extracting pages 51-111: {e}")
            return input_path
    
    def is_available(self):
        return self.extractor is not None
    def get_schema(self):
        """Returns the clinical study protocol schema"""
        return get_clinical_study_protocol_schema()
    
    def extract_from_buffer(self, file_buffer, filename):
        """Extract clinical study protocol data from PDF buffer"""
        if not self.is_available():
            return {"success": False, "error": "LlamaExtract service not available. Check API key and dependencies."}
            
        # Validate inputs
        if not file_buffer:
            return {"success": False, "error": "No file buffer provided"}
            
        import tempfile
        import uuid
        
        temp_file_path = None
        try:
            print(f"\n[LlamaExtract] Starting clinical study protocol extraction for file: {filename}")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                file_buffer.seek(0)
                temp_file.write(file_buffer.read())
                temp_file_path = temp_file.name
            
            print(f"[LlamaExtract] Created temp file: {temp_file_path}")
            
            # Extract pages 20-40 to a new temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='_pages_20_40.pdf') as pages_file:
                pages_file_path = pages_file.name
            
            # Extract specific pages
            final_file_path = self.extract_pages_20_to_40(temp_file_path, pages_file_path)
            
            # Check if temp file was created successfully
            if not os.path.exists(final_file_path) or os.path.getsize(final_file_path) == 0:
                return {"success": False, "error": "Failed to create temporary file or extract pages 20-40"}
            
            file_size = os.path.getsize(final_file_path)
            print(f"[LlamaExtract] Processing file size: {file_size} bytes")
            
            # Get clinical study protocol schema
            try:
                schema = self.get_schema()
                print(f"[LlamaExtract] Using clinical study protocol schema")
            except Exception as e:
                return {"success": False, "error": f"Failed to load schema: {str(e)}"}
            
            # Create unique agent name
            unique_name = f"clinical-protocol-extractor-{uuid.uuid4().hex[:8]}"
            print(f"[LlamaExtract] Agent name: {unique_name}")
            
            # Create agent and extract
            print(f"[LlamaExtract] Creating extraction agent...")
            agent = self.extractor.create_agent(name=unique_name, data_schema=schema)
            
            print(f"[LlamaExtract] Running extraction on pages 20-40...")
            # Extract only pages 20-40
            result = agent.extract(final_file_path)
            
            # Log the extraction results
            print("\n" + "="*50)
            print("CLINICAL STUDY PROTOCOL EXTRACTION RESULTS:")
            print("="*50)
            print(f"File: {filename}")
            print(f"Result: {result.data}")
            print("="*50 + "\n")
            
            # Clinical protocol template data
            clinical_protocol_template = {
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
                ]
            }
            
            # Combine protocol template with extracted data
            response_data = {
                "protocol_template": clinical_protocol_template,
                "extracted_content": result.data,
                "pages_processed": "20-40"
            }
            
            return {
                "success": True, 
                "data": response_data,
                "filename": filename,
                "schema_type": "clinical_study_protocol",
                "agent_name": unique_name
            }
            
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            print(f"\n[LlamaExtract ERROR] {error_msg}")
            print(f"[LlamaExtract ERROR] Exception type: {type(e).__name__}")
            return {"success": False, "error": error_msg}
            
        finally:
            # Clean up temporary files
            for file_path in [temp_file_path, pages_file_path]:
                if file_path and os.path.exists(file_path):
                    try:
                        os.unlink(file_path)
                        print(f"[LlamaExtract] Cleaned up temp file: {file_path}")
                    except Exception as e:
                        print(f"[LlamaExtract] Failed to cleanup temp file: {e}")

# Service instance
llama_service = LlamaExtractService()