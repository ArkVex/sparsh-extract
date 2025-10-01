import os
import io
from typing import Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

try:
    from llama_cloud_services import LlamaExtract
    LLAMA_EXTRACT_AVAILABLE = True
except ImportError:
    print("Warning: llama-cloud-services not available. Install with: pip install llama-cloud-services")
    LLAMA_EXTRACT_AVAILABLE = False

load_dotenv()

# =============================================================================
# ORIGINAL SCHEMAS
# =============================================================================

def get_clinical_study_protocol_schema():
    """
    Original schema for clinical study protocol extraction.
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

def get_schedule_of_activities_schema():
    """
    Original schema for schedule of activities extraction.
    """
    class Milestone(BaseModel):
        milestone_name: Optional[str] = None
        milestone_date: Optional[str] = None

    class Activity(BaseModel):
        activity_id: Optional[str] = None
        activity_name: str
        description: Optional[str] = None
        category: Optional[str] = None
        responsible_party: Optional[str] = None
        dependencies: Optional[List[str]] = None
        start_date: Optional[str] = None
        end_date: Optional[str] = None
        duration: Optional[str] = None
        milestones: Optional[List[Milestone]] = None
        status: Optional[str] = None
        notes: Optional[str] = None

    class ScheduleOfActivities(BaseModel):
        project_title: Optional[str] = None
        project_id: Optional[str] = None
        activities: List[Activity]
        overall_start_date: Optional[str] = None
        overall_end_date: Optional[str] = None
        created_by: Optional[str] = None
        last_updated: Optional[str] = None

    return ScheduleOfActivities

# =============================================================================
# COMPREHENSIVE CLINICAL STUDY SCHEMA (Protocol + Data Combined)
# =============================================================================

def get_comprehensive_clinical_study_schema():
    """
    Returns a comprehensive schema combining both clinical study protocol and clinical study data
    for unified extraction from clinical documents.
    """
    from pydantic import BaseModel, Field
    from typing import Optional, List
    from enum import Enum

    class SexEnum(str, Enum):
        male = "male"
        female = "female"
        other = "other"

    class PerformanceStatusEnum(str, Enum):
        ECOG_0 = "ECOG 0"
        ECOG_1 = "ECOG 1"
        ECOG_2 = "ECOG 2"
        ECOG_3 = "ECOG 3"
        ECOG_4 = "ECOG 4"

    class ClinicalOutcomeEnum(str, Enum):
        PRO = "PRO"
        PRO_CTCAE = "PRO-CTCAE"
        PGI = "PGI"
        PROMIS = "PROMIS"
        NSCLC_SAQ = "NSCLC-SAQ"
        EORTC = "EORTC"
        EQ_5D_5L = "EQ-5D-5L"
        HOSPAD = "HOSPAD"

    class StudyInterventionEnum(str, Enum):
        Rilvegostomig = "Rilvegostomig"
        Pembrolizumab = "Pembrolizumab"
        Carboplatin = "Carboplatin"
        Paclitaxel = "Paclitaxel"
        Nab_paclitaxel = "Nab-paclitaxel"

    # Protocol Information Classes
    class ProtocolActivity(BaseModel):
        category: str = Field(description="The grouping category for the procedure, e.g., 'Laboratory Assessments', 'Biomarker assessments'.")
        procedure_name: str = Field(description="The specific name of the procedure, e.g., 'Full physical examination', 'Hematology'.")
        visit_schedule: str = Field(description="When this procedure occurs, e.g., 'Screening Day -28 to -1', 'Cycle 1 Day 1', 'Every 12 weeks'.")
        notes: Optional[str] = Field(None, description="Any special conditions or notes for this procedure.")
        protocol_section: Optional[str] = Field(None, description="Protocol section reference, e.g., 'Section 8.3.1'.")

    class ProtocolInformation(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where protocol information is found")
        protocol_title: Optional[str] = Field(None, description="The official title of the study.")
        sponsor: Optional[str] = Field(None, description="The sponsoring organization name.")
        protocol_version: Optional[str] = Field(None, description="The protocol document version.")
        intervention_activities: List[ProtocolActivity] = Field(default_factory=list, description="Procedures and assessments during the intervention period.")
        post_intervention_activities: List[ProtocolActivity] = Field(default_factory=list, description="Procedures and assessments during post-intervention follow-up.")
        footnotes: Optional[str] = Field(None, description="Important footnotes from the schedule of activities.")
        abbreviations: Optional[str] = Field(None, description="Key abbreviations and their definitions.")

    # Clinical Data Classes (existing ones)
    class InformedConsent(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where this information is found (e.g., '5.1', '4.2')")
        mainStudy: bool = Field(description="Whether informed consent for main study is required")
        geneticSampleOptional: Optional[bool] = Field(None, description="Whether genetic sample consent is optional")

    class EligibilityCriteria(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where eligibility criteria are found (e.g., '5.1', '5.2')")
        inclusion: List[str] = Field(description="List of inclusion criteria")
        exclusion: List[str] = Field(description="List of exclusion criteria")
        temporaryDelaySection: Optional[str] = Field(None, description="Section number for temporary delay criteria (e.g., '5.5')")
        temporaryDelayCriteria: List[str] = Field(default_factory=list, description="Criteria for temporarily delaying enrollment/randomization/administration")

    class Randomization(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where randomization is described (e.g., '6.3')")
        method: Optional[str] = Field(None, description="Randomization method")
        sectionReference: Optional[str] = Field(None, description="Protocol section reference for randomization")

    class Demography(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where demographic requirements are found")
        age: Optional[int] = Field(None, description="Patient age")
        sex: Optional[SexEnum] = Field(None, description="Patient sex")
        ethnicity: Optional[str] = Field(None, description="Patient ethnicity")
        race: Optional[str] = Field(None, description="Patient race")

    class VitalSigns(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where vital signs procedures are described (e.g., '8.3.2')")
        temperature: Optional[float] = Field(None, description="Body temperature")
        heartRate: Optional[float] = Field(None, description="Heart rate (bpm)")
        bloodPressure: Optional[str] = Field(None, description="Blood pressure (systolic/diastolic)")
        respiratoryRate: Optional[float] = Field(None, description="Respiratory rate (breaths per minute)")
        SpO2: Optional[float] = Field(None, description="Oxygen saturation (%)")

    class PhysicalExamination(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where physical examination procedures are described (e.g., '8.3.1')")
        fullExam: Optional[bool] = Field(None, description="Whether full physical examination is performed")
        targetedExam: Optional[bool] = Field(None, description="Whether targeted examination is performed")
        height_cm: Optional[float] = Field(None, description="Patient height in centimeters")
        weight_kg: Optional[float] = Field(None, description="Patient weight in kilograms")
        vitalSigns: Optional[VitalSigns] = Field(None, description="Vital signs measurements")

    class CardiacAssessments(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where cardiac assessments are described (e.g., '8.3.3', '8.3.5.1')")
        ECG_12lead: Optional[bool] = Field(None, description="Whether 12-lead ECG is performed")
        LVEF: Optional[float] = Field(None, description="Left ventricular ejection fraction (%) from ECHO/MUGA")

    class SafetyMonitoring(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where safety monitoring procedures are described (e.g., '8.4', '6.9')")
        AE_review: Optional[bool] = Field(None, description="Whether adverse events are reviewed")
        concomitantMedications: List[str] = Field(default_factory=list, description="List of concomitant medications")

    class LaboratoryAssessments(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where laboratory assessments are described (e.g., '8.3.4', 'Appendix G')")
        pregnancyTest: Optional[bool] = Field(None, description="Whether pregnancy test is performed")
        tuberculosis: Optional[bool] = Field(None, description="Whether tuberculosis testing is performed")
        HIV: Optional[bool] = Field(None, description="Whether HIV testing is performed")
        hepatitis: Optional[bool] = Field(None, description="Whether hepatitis testing is performed")
        chemistryPanel: Optional[bool] = Field(None, description="Whether chemistry panel is performed")
        hematology: Optional[bool] = Field(None, description="Whether hematology testing is performed")
        coagulation: Optional[bool] = Field(None, description="Whether coagulation testing is performed")
        thyroid: Optional[bool] = Field(None, description="Whether thyroid testing is performed")
        troponin: Optional[bool] = Field(None, description="Whether troponin testing is performed")
        urinalysis: Optional[bool] = Field(None, description="Whether urinalysis is performed")

    class Pharmacokinetics(BaseModel):
        sectionNumber: Optional[str] = Field(None, description="Section number where pharmacokinetic procedures are described (e.g., '8.5')")
        preDoseSamples: Optional[bool] = Field(None, description="Whether pre-dose samples are collected")
        otherNotes: Optional[str] = Field(None, description="Additional pharmacokinetic notes")

    class ComprehensiveClinicalStudy(BaseModel):
        # Protocol Information Section
        protocolInformation: Optional[ProtocolInformation] = Field(None, description="Protocol metadata and activity schedules")
        
        # Clinical Data Section
        informedConsent: InformedConsent = Field(description="Informed consent requirements")
        studyProcedures: List[str] = Field(default_factory=list, description="List of procedures and safety assessments")
        eligibilityCriteria: EligibilityCriteria = Field(description="Inclusion and exclusion criteria")
        randomization: Optional[Randomization] = Field(None, description="Randomization details")
        demography: Demography = Field(description="Demographic information")
        medicalHistory: List[str] = Field(default_factory=list, description="Past or current medical conditions, including surgical history")
        performanceStatus: Optional[PerformanceStatusEnum] = Field(None, description="ECOG performance status")
        physicalExamination: Optional[PhysicalExamination] = Field(None, description="Physical examination details")
        cardiacAssessments: Optional[CardiacAssessments] = Field(None, description="Cardiac assessment details")
        safetyMonitoring: Optional[SafetyMonitoring] = Field(None, description="Safety monitoring procedures")
        laboratoryAssessments: Optional[LaboratoryAssessments] = Field(None, description="Laboratory assessment details")
        pharmacokinetics: Optional[Pharmacokinetics] = Field(None, description="Pharmacokinetic sampling details")
        tumorImaging: List[str] = Field(default_factory=list, description="Imaging methods such as CT, MRI, PET")
        clinicalOutcomeAssessments: List[ClinicalOutcomeEnum] = Field(default_factory=list, description="Clinical outcome assessment tools")
        studyIntervention: List[StudyInterventionEnum] = Field(description="Study intervention medications")

    return ComprehensiveClinicalStudy

# =============================================================================
# SCHEMA SELECTOR
# =============================================================================

def get_schema(schema_type="comprehensive_clinical_study"):
    """
    Returns the appropriate schema based on the type requested.
    
    Available schemas:
    - "clinical_study_protocol": Original protocol schema
    - "schedule_of_activities": Original activities schema  
    - "comprehensive_clinical_study": New comprehensive schema (protocol + data combined)
    """
    if schema_type == "clinical_study_protocol":
        return get_clinical_study_protocol_schema()
    elif schema_type == "schedule_of_activities":
        return get_schedule_of_activities_schema()
    elif schema_type == "comprehensive_clinical_study":
        return get_comprehensive_clinical_study_schema()
    else:
        # Default to comprehensive schema
        return get_comprehensive_clinical_study_schema()

# =============================================================================
# SERVICE CLASSES (Legacy - for compatibility)
# =============================================================================

class LlamaExtractService:
    """
    LlamaExtract service for structured data extraction from PDFs.
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
    
    def is_available(self):
        return self.extractor is not None
    
    def get_schema(self, schema_type):
        return get_schema(schema_type)
    
    def extract_from_buffer(self, file_buffer, filename, schema_type="comprehensive_clinical_study"):
        if not self.is_available():
            return {"success": False, "error": "LlamaExtract service not available. Check API key and dependencies."}
            
        # Validate inputs
        if not file_buffer:
            return {"success": False, "error": "No file buffer provided"}
            
        import tempfile
        import uuid
        
        temp_file_path = None
        try:
            print(f"\n[LlamaExtract] Starting extraction for file: {filename}")
            print(f"[LlamaExtract] Schema type: {schema_type}")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                file_buffer.seek(0)
                temp_file.write(file_buffer.read())
                temp_file_path = temp_file.name
            
            print(f"[LlamaExtract] Created temp file: {temp_file_path}")
            
            # Check if temp file was created successfully
            if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
                return {"success": False, "error": "Failed to create temporary file"}
            
            file_size = os.path.getsize(temp_file_path)
            print(f"[LlamaExtract] Temp file size: {file_size} bytes")
            
            # Get schema
            try:
                schema = self.get_schema(schema_type)
                print(f"[LlamaExtract] Using schema: {schema}")
            except Exception as e:
                return {"success": False, "error": f"Invalid schema type '{schema_type}': {str(e)}"}
            
            # Create unique agent name
            unique_name = f"clinical-extractor-{uuid.uuid4().hex[:8]}"
            print(f"[LlamaExtract] Agent name: {unique_name}")
            
            # Create agent and extract
            print(f"[LlamaExtract] Creating extraction agent...")
            agent = self.extractor.create_agent(name=unique_name, data_schema=schema)
            
            print(f"[LlamaExtract] Running extraction...")
            result = agent.extract(temp_file_path)
            
            # Log the extraction results
            print("\n" + "="*50)
            print("LLAMAEXTRACT RESULTS:")
            print("="*50)
            print(f"File: {filename}")
            print(f"Schema: {schema_type}")
            print(f"Result: {result.data}")
            print("="*50 + "\n")
            
            return {
                "success": True, 
                "data": result.data,
                "filename": filename,
                "schema_type": schema_type,
                "agent_name": unique_name
            }
            
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            print(f"\n[LlamaExtract ERROR] {error_msg}")
            print(f"[LlamaExtract ERROR] Exception type: {type(e).__name__}")
            return {"success": False, "error": error_msg}
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    print(f"[LlamaExtract] Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    print(f"[LlamaExtract] Failed to cleanup temp file: {e}")

# Service instances
llama_service = LlamaExtractService()