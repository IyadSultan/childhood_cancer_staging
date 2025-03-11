import os
import json
from crewai import Agent
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# disable crewai telemetry from https://www.reddit.com/r/crewai/comments/1cp5gby/how_can_i_disable_all_telemetry_in_crewai/
from crewai.telemetry import Telemetry

# Add import from our new module
from .azure_openai_config import get_azure_openai_llm

def noop(*args, **kwargs):
    pass

def disable_crewai_telemetry():
    for attr in dir(Telemetry):
        if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
            setattr(Telemetry, attr, noop)

# Disable telemetry immediately
disable_crewai_telemetry()

# Get the path to the toronto_staging.json file
def get_staging_data_path() -> str:
    """Get the path to the Toronto staging data JSON file."""
    # Default path relative to the current directory
    default_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'toronto_staging.json'
    )
    
    # Check if the file exists
    if not os.path.exists(default_path):
        # Try alternative paths
        alt_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                         'pediatric_staging', 'toronto_staging.json'),
        ]
        
        for path in alt_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError("Toronto staging data file not found")
    
    return default_path

# Load the staging data
try:
    staging_data_path = get_staging_data_path()
    with open(staging_data_path, 'r') as f:
        TORONTO_STAGING_DATA = json.load(f)
except Exception as e:
    print(f"Error loading staging data: {e}")
    TORONTO_STAGING_DATA = {}

# Define cancers covered by Toronto Pediatric Cancer Staging System from the JSON file
TORONTO_COVERED_CANCERS = list(TORONTO_STAGING_DATA.keys())

# Create stage mapping to ensure correct stage terminology is used
STAGE_TERMINOLOGY = {}
for cancer_type, data in TORONTO_STAGING_DATA.items():
    STAGE_TERMINOLOGY[cancer_type] = list(data.get("stages", {}).keys())

# Define mapping from specific cancer types to their standardized Toronto categories
CANCER_TYPE_MAPPING = {
    # Non-Hodgkin lymphoma variants
    "burkitt lymphoma": "Non-Hodgkin Lymphoma",
    "burkitt's lymphoma": "Non-Hodgkin Lymphoma",
    "anaplastic large cell lymphoma": "Non-Hodgkin Lymphoma", 
    "lymphoblastic lymphoma": "Non-Hodgkin Lymphoma",
    "diffuse large b-cell lymphoma": "Non-Hodgkin Lymphoma",
    "primary mediastinal b-cell lymphoma": "Non-Hodgkin Lymphoma",
    "dlbcl": "Non-Hodgkin Lymphoma",
    
    # Ewing sarcoma family
    "ewing sarcoma": "Bone Tumors",
    "ewing's sarcoma": "Bone Tumors",
    "primitive neuroectodermal tumor": "Bone Tumors",
    "pnet": "Bone Tumors",
    "askin tumor": "Bone Tumors",
    "osteosarcoma": "Bone Tumors",
    
    # Wilms tumor and renal tumors variants
    "nephroblastoma": "Renal Tumors",
    "wilms": "Renal Tumors",
    "wilm's tumor": "Renal Tumors",
    "wilms' tumor": "Renal Tumors",
    "clear cell sarcoma": "Renal Tumors",
    "rhabdoid tumor (kidney)": "Renal Tumors",
    
    # Specific testicular germ cell tumors
    "testicular yolk sac tumor": "Testicular Germ Cell Tumor",
    "testicular teratoma": "Testicular Germ Cell Tumor",
    "testicular dysgerminoma": "Testicular Germ Cell Tumor",
    "testicular seminoma": "Testicular Germ Cell Tumor",
    "testicular embryonal carcinoma": "Testicular Germ Cell Tumor",
    "testicular choriocarcinoma": "Testicular Germ Cell Tumor",
    "testicular mixed germ cell tumor": "Testicular Germ Cell Tumor",
    
    # Specific ovarian germ cell tumors
    "ovarian yolk sac tumor": "Ovarian Germ Cell Tumor",
    "ovarian teratoma": "Ovarian Germ Cell Tumor",
    "ovarian dysgerminoma": "Ovarian Germ Cell Tumor",
    "ovarian seminoma": "Ovarian Germ Cell Tumor",
    "ovarian embryonal carcinoma": "Ovarian Germ Cell Tumor",
    "ovarian choriocarcinoma": "Ovarian Germ Cell Tumor",
    "ovarian mixed germ cell tumor": "Ovarian Germ Cell Tumor",

    # Leukemia subtypes
    "b-cell all": "Acute Lymphoblastic Leukemia",
    "t-cell all": "Acute Lymphoblastic Leukemia",
    "b-precursor all": "Acute Lymphoblastic Leukemia",
    "b-lymphoblastic leukemia": "Acute Lymphoblastic Leukemia",
    "t-lymphoblastic leukemia": "Acute Lymphoblastic Leukemia",
    "all": "Acute Lymphoblastic Leukemia",
    
    # Non-rhabdomyosarcoma soft tissue sarcoma variants
    "synovial sarcoma": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "fibrosarcoma": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "liposarcoma": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "malignant peripheral nerve sheath tumor": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "mpnst": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "desmoplastic small round cell tumor": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "epithelioid sarcoma": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "alveolar soft part sarcoma": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "clear cell sarcoma": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    "nrsts": "Non-Rhabdomyosarcoma Soft Tissue Sarcoma",
    
    # Rhabdomyosarcoma variants
    "embryonal rhabdomyosarcoma": "Rhabdomyosarcoma",
    "alveolar rhabdomyosarcoma": "Rhabdomyosarcoma",
    "pleomorphic rhabdomyosarcoma": "Rhabdomyosarcoma",
    "spindle cell rhabdomyosarcoma": "Rhabdomyosarcoma",
    
    # Hodgkin lymphoma variants
    "classical hodgkin lymphoma": "Hodgkin Lymphoma",
    "nodular sclerosis hodgkin lymphoma": "Hodgkin Lymphoma",
    "mixed cellularity hodgkin lymphoma": "Hodgkin Lymphoma",
    "lymphocyte-rich hodgkin lymphoma": "Hodgkin Lymphoma",
    "lymphocyte-depleted hodgkin lymphoma": "Hodgkin Lymphoma",
    "nodular lymphocyte predominant hodgkin lymphoma": "Hodgkin Lymphoma",
    "lymphocyte predominant hodgkin lymphoma": "Hodgkin Lymphoma",

    # astrocytoma variants
    "astrocytoma": "Astrocytoma",
    "pilocytic astrocytoma": "Astrocytoma",
    "glioma": "Astrocytoma",
    "glioblastoma": "Astrocytoma",
    "gliosarcoma": "Astrocytoma",
    "gliomatosis cerebri": "Astrocytoma",

    # Medulloblastoma variants
    "medulloblastoma": "Medulloblastoma",
    "nodular medulloblastoma": "Medulloblastoma",
    "diffuse medulloblastoma": "Medulloblastoma",
    "anaplastic medulloblastoma": "Medulloblastoma",

    # neuroblastoma variants
    "neuroblastoma": "Neuroblastoma",
    "ganglioneuroblastoma": "Neuroblastoma",
    "ganglioneuroma": "Neuroblastoma",
}

def format_mapping_for_agent(mapping_dict):
    """
    Formats the mapping dictionary into a readable string for agent backstories.
    """
    mapping_text = ""
    for subtype, category in mapping_dict.items():
        mapping_text += f"- '{subtype}' maps to '{category}'\n"
    return mapping_text

def lookup_cancer_type(specific_type, mapping_dict=CANCER_TYPE_MAPPING):
    """
    Looks up the standardized Toronto category for a specific cancer type.
    
    Args:
        specific_type: The specific cancer subtype to look up
        mapping_dict: The mapping dictionary to use
        
    Returns:
        The standardized Toronto category, or None if not found
    """
    return mapping_dict.get(specific_type.lower(), None)

def get_valid_stages_for_cancer(cancer_type):
    """
    Get the valid stage names for a given cancer type from toronto_staging.json.
    
    Args:
        cancer_type: The standardized cancer type
    
    Returns:
        List of valid stage names
    """
    if cancer_type in STAGE_TERMINOLOGY:
        return STAGE_TERMINOLOGY[cancer_type]
    return []

def format_valid_stages(cancer_type):
    """Format valid stages for a cancer type as a readable string."""
    stages = get_valid_stages_for_cancer(cancer_type)
    if not stages:
        return "No staging information available"
    
    return f"Valid stages for {cancer_type}: {', '.join(stages)}"

class CancerStagingAgents:
    """
    Provides agents for pediatric cancer staging tasks.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the cancer staging agents.
        
        Args:
            model (str): The Azure OpenAI model deployment name to use
        """
        self.model = model  # Store raw model name
        self.deployment_name = os.getenv("AZURE_GPT4O_DEPLOYMENT", model)
        self.azure_model = f"azure/{self.deployment_name}"  # Format for CrewAI
        
        self.mapping_text = format_mapping_for_agent(CANCER_TYPE_MAPPING)
        
        # Create a reference text for stage terminology
        self.stage_terminology_text = ""
        for cancer, stages in STAGE_TERMINOLOGY.items():
            self.stage_terminology_text += f"{cancer}: {', '.join(stages)}\n"
        
        # Get a configured LLM for direct LangChain use
        self.llm = get_azure_openai_llm(deployment_name=self.deployment_name)
    
    def create_cancer_identifier_agent(self) -> Agent:
        """
        Creates an agent specialized in identifying cancer types.
        """
        return Agent(
            role="Pediatric Oncology Expert",
            goal="Identify the cancer type from medical notes and verify if it's covered by the Toronto Staging System",
            backstory=f"""You are a pediatric oncologist with expertise in identifying 
            cancer types from medical records. You are highly skilled at extracting 
            key diagnostic information, even when spread across multiple documents.
            
            You are also familiar with the Toronto Pediatric Cancer Staging System and know that
            it ONLY covers the following standardized cancer types (loaded directly from toronto_staging.json):
            {', '.join(TORONTO_COVERED_CANCERS)}.

            You understand that many specific cancer subtypes need to be mapped to these standardized categories.
            Here's the mapping of specific cancer types to their standardized categories:
            
            {self.mapping_text}
            
            Always check if an identified cancer subtype maps to one of the standardized Toronto categories.
            
            If you identify a cancer type that does NOT map to any Toronto category AND is not directly listed 
            in the Toronto covered cancers, explicitly state:
            "THIS CANCER TYPE IS NOT COVERED BY THE TORONTO PEDIATRIC CANCER STAGING SYSTEM"
            at the beginning of your analysis.""",
            tools=[],
            verbose=True,
            llm=self.llm,  # Use LangChain LLM
            llm_config={"model": self.azure_model}  # Provide fallback CrewAI config
        )
        
    def create_criteria_analyzer_agent(self) -> Agent:
        """
        Creates an agent specialized in analyzing staging criteria from medical notes.
        """
        return Agent(
            role="Cancer Staging Specialist",
            goal="Analyze medical notes for cancer staging criteria according to the Toronto Staging System",
            backstory=f"""You are a cancer staging specialist with expertise in the Toronto 
            Pediatric Cancer Staging System. You carefully analyze medical notes to identify 
            key findings that determine the disease stage.
            
            You know the specific criteria needed for each cancer type and stage, including:
            - Tumor size, location, and extent
            - Lymph node involvement
            - Presence of metastases
            - Surgical findings and resectability
            - Specific biological and histological features
            
            For CNS tumors, you understand the importance of Chang staging for medulloblastoma and WHO grading.
            
            For leukemias, you understand CNS classification (CNS1, CNS2, CNS3) and extramedullary involvement.
            
            You also understand stage terminology for each cancer type:
            {self.stage_terminology_text}
            
            Your role is to extract all staging-relevant information from medical notes in an 
            organized and comprehensive manner.""",
            tools=[],
            verbose=True,
            llm=self.llm
        )
        
    def create_stage_calculator_agent(self) -> Agent:
        """
        Creates an agent specialized in calculating cancer stages based on the analyzed criteria.
        """
        return Agent(
            role="Pediatric Oncology Staging Expert",
            goal="Determine the precise cancer stage based on Toronto Staging criteria",
            backstory=f"""You are a pediatric oncology staging expert with extensive knowledge 
            of the Toronto Pediatric Cancer Staging System. Your specialty is interpreting 
            clinical findings and determining the exact stage of cancer according to 
            standardized criteria.
            
            You understand the nuances of different staging systems used for different 
            pediatric cancers, including:
            
            - Ann Arbor for lymphomas
            - International Staging System for Wilms tumor
            - INSS for neuroblastoma
            - TNM and AJCC systems where applicable
            - Chang staging for medulloblastoma
            - FIGO staging for ovarian tumors
            
            You also understand stage terminology for each cancer type:
            {self.stage_terminology_text}
            
            Your expertise allows you to precisely match clinical findings to staging criteria,
            and you're careful to note when criteria are met partially or not at all.""",
            tools=[],
            verbose=True,
            llm=self.llm
        )
        
    def create_report_generator_agent(self) -> Agent:
        """
        Creates an agent specialized in generating staging reports.
        """
        return Agent(
            role="Medical Documentation Specialist",
            goal="Generate comprehensive and accurate staging reports for pediatric cancer cases",
            backstory="""You are a medical documentation specialist with expertise in oncology 
            reporting. You excel at synthesizing complex medical findings into clear, 
            structured reports that follow standard medical documentation guidelines.
            
            Your reports are precise, comprehensive, and designed to communicate essential 
            staging information effectively to healthcare providers. You highlight important 
            discrepancies between EMR-recorded stages and calculated stages, and clearly 
            explain the rationale for the staging determination.
            
            You ensure all reports include the filename, EMR-recorded stage (if available), 
            calculated stage, and a thorough explanation.""",
            tools=[],
            verbose=True,
            llm=self.llm
        )

def format_staging_results(emr_stage, calculated_stage, explanation):
    """Format staging results without CSV headers or filenames"""
    formatted_output = f"""
# Pediatric Cancer Staging Results

## EMR Stage: {emr_stage}
## Calculated Stage: {calculated_stage}

### Explanation:

{explanation}
"""
    return formatted_output 