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
            
            print(f"[LlamaExtract] Running extraction on pages 51-111...")
            # Extract only pages 51-111
            result = agent.extract(final_file_path)
            
            # Log the extraction results
            print("\n" + "="*50)
            print("CLINICAL STUDY PROTOCOL EXTRACTION RESULTS:")
            print("="*50)
            print(f"File: {filename}")
            print(f"Result: {result.data}")
            print("="*50 + "\n")
            
            return {
                "success": True, 
                "data": result.data,
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