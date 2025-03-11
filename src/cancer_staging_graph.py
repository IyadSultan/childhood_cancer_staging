"""
LangGraph implementation of cancer staging workflow
"""

import json
import os
import logging
from typing import Annotated, Dict, List, Any, Optional
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from .azure_openai_config import get_azure_openai_llm, get_llm_with_system_prompt

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define state schema for our workflow
class CancerStagingState(TypedDict):
    """State for the cancer staging workflow"""
    messages: Annotated[List, add_messages]  # Conversation history
    medical_note: str  # The medical note text
    cancer_type: Optional[str]  # Identified cancer type
    standardized_cancer_type: Optional[str]  # Mapped to Toronto categories
    is_covered_by_toronto: Optional[bool]  # Whether this cancer is covered
    identified_criteria: Optional[Dict]  # Staging criteria identified in the note
    stage: Optional[str]  # Determined stage
    explanation: Optional[str]  # Explanation of staging
    report: Optional[str]  # Final report
    primary_site: str  # Primary site of the cancer
    metastasis_sites: str  # Any mentioned sites of metastasis
    extracted_stage: str  # Any explicitly mentioned stage in the note

# Helper functions for cancer mapping
def load_toronto_staging_data():
    """Load the Toronto staging data from the JSON file"""
    try:
        # Try to load from default location
        default_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'toronto_staging.json'
        )
        
        # If not found, try alternative locations
        if not os.path.exists(default_path):
            alt_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'toronto_staging.json'),
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    default_path = path
                    break
                    
        # Load the data
        with open(default_path, 'r') as f:
            data = json.load(f)
            logger.info(f"Successfully loaded staging data from {default_path}")
            return data
    except Exception as e:
        logger.error(f"Error loading Toronto staging data: {e}")
        # Return empty dict if file not found
        return {}

# Load staging data
TORONTO_STAGING_DATA = load_toronto_staging_data()
TORONTO_COVERED_CANCERS = list(TORONTO_STAGING_DATA.keys())

# Cancer mapping for standard terminology
def get_cancer_mapping_text():
    """Format cancer mapping for use in prompts"""
    from src.agents import CANCER_TYPE_MAPPING
    
    mapping_text = ""
    for specific, standard in CANCER_TYPE_MAPPING.items():
        mapping_text += f"- {specific} → {standard}\n"
    
    return mapping_text

# Cancer stages reference text
def get_stage_terminology_text():
    """Format stage terminology for use in prompts"""
    stage_terminology_text = ""
    for cancer_type, data in TORONTO_STAGING_DATA.items():
        stages = list(data.get("stages", {}).keys())
        stage_terminology_text += f"{cancer_type}: {', '.join(stages)}\n"
    
    return stage_terminology_text

# Node functions for our workflow
def identify_cancer_type(state: CancerStagingState):
    """Identify cancer type from medical note"""
    llm = get_llm_with_system_prompt(
        system_prompt=f"""You are a pediatric oncologist specialized in identifying cancer types from medical notes.
        You extract information about cancer diagnoses in pediatric patients and map them to standardized categories.
        
        The Toronto Pediatric Cancer Staging System ONLY covers these cancer types:
        {', '.join(TORONTO_COVERED_CANCERS)}
        
        Here is the mapping from specific diagnoses to their standardized categories:
        {get_cancer_mapping_text()}
        
        Always check if an identified cancer type maps to one of the standardized Toronto categories.
        
        ADDITIONALLY, please extract:
        1. Primary site (location) of the cancer
        2. Any mentioned sites of metastasis
        3. Any explicitly mentioned stage in the note (e.g., "Stage III")
        """
    )
    
    # Prepare user message with the medical note
    user_message = HumanMessage(
        content=f"Please analyze this medical note and identify the cancer type and additional information. If multiple cancer types are mentioned, identify the primary diagnosis.\n\nMedical Note:\n{state['medical_note']}"
    )
    
    # Call the LLM to identify cancer type
    response = llm([user_message])
    
    # Parse response to extract information
    # For a real implementation, you would use a structured output parser
    content = response.content
    cancer_type = content.split("Cancer Type:")[1].split("\n")[0].strip() if "Cancer Type:" in content else None
    standardized_type = content.split("Standardized Category:")[1].split("\n")[0].strip() if "Standardized Category:" in content else None
    is_covered = "NOT COVERED BY THE TORONTO PEDIATRIC CANCER STAGING SYSTEM" not in content
    
    # Extract additional information
    primary_site = content.split("Primary Site:")[1].split("\n")[0].strip() if "Primary Site:" in content else "Not specified"
    metastasis_sites = content.split("Metastasis Sites:")[1].split("\n")[0].strip() if "Metastasis Sites:" in content else "None identified"
    extracted_stage = content.split("Extracted Stage:")[1].split("\n")[0].strip() if "Extracted Stage:" in content else "Not mentioned"
    
    # Update state
    return {
        "cancer_type": cancer_type,
        "standardized_cancer_type": standardized_type,
        "is_covered_by_toronto": is_covered,
        "primary_site": primary_site,
        "metastasis_sites": metastasis_sites,
        "extracted_stage": extracted_stage,
        "messages": [user_message, response]
    }

def analyze_staging_criteria(state: CancerStagingState):
    """Analyze staging criteria for the identified cancer"""
    if not state.get("is_covered_by_toronto", False):
        # Skip if cancer is not covered by Toronto system
        return {
            "identified_criteria": {},
            "messages": [
                HumanMessage(content=f"This cancer type ({state.get('cancer_type', 'Unknown')}) is not covered by the Toronto Pediatric Cancer Staging System."),
                AIMessage(content="I cannot perform staging as this cancer type is not covered by the Toronto Pediatric Cancer Staging System.")
            ]
        }
    
    # Get cancer-specific staging information
    cancer_type = state.get("standardized_cancer_type") or state.get("cancer_type")
    staging_info = TORONTO_STAGING_DATA.get(cancer_type, {})
    
    # Create LLM with appropriate system prompt
    llm = get_llm_with_system_prompt(
        system_prompt=f"""You are a pediatric oncology staging specialist. 
        You analyze medical notes to identify specific staging criteria for {cancer_type} 
        according to the Toronto Pediatric Cancer Staging System.
        
        For {cancer_type}, the valid stages are:
        {get_stage_terminology_text()}
        """
    )
    
    # Prepare user message
    user_message = HumanMessage(
        content=f"""Please analyze this medical note and identify which staging criteria for {cancer_type} are present.
        
        Medical Note:
        {state['medical_note']}
        
        Toronto staging criteria for {cancer_type}:
        {json.dumps(staging_info, indent=2)}
        
        Extract all relevant information that can be used for staging this cancer.
        """
    )
    
    # Call the LLM to analyze criteria
    response = llm([user_message])
    
    # Parse response to extract criteria (simplified)
    # In a real implementation, you would use structured output parsing
    return {
        "identified_criteria": {"raw_analysis": response.content},
        "messages": [user_message, response]
    }

def calculate_stage(state: CancerStagingState):
    """Calculate cancer stage based on identified criteria"""
    if not state.get("is_covered_by_toronto", False):
        # Skip if cancer is not covered
        return {
            "stage": "Not applicable",
            "explanation": "This cancer type is not covered by the Toronto Pediatric Cancer Staging System.",
            "messages": []
        }
    
    # Create LLM with appropriate system prompt
    cancer_type = state.get("standardized_cancer_type") or state.get("cancer_type")
    staging_info = TORONTO_STAGING_DATA.get(cancer_type, {})
    
    llm = get_llm_with_system_prompt(
        system_prompt=f"""You are a pediatric oncology staging expert specializing in the Toronto Pediatric Cancer Staging System.
        You determine the stage for {cancer_type} based on the criteria present in medical notes.
        
        For {cancer_type}, the valid stages and their criteria are:
        {json.dumps(staging_info, indent=2)}
        """
    )
    
    # Prepare user message
    user_message = HumanMessage(
        content=f"""Based on the following criteria analysis, determine the Toronto stage for this {cancer_type} case.
        
        Medical Note:
        {state['medical_note']}
        
        Criteria Analysis:
        {state.get('identified_criteria', {}).get('raw_analysis', 'No analysis available')}
        
        Please provide:
        1. The determined stage
        2. A detailed explanation of how you determined this stage
        """
    )
    
    # Call the LLM to calculate stage
    response = llm([user_message])
    
    # Parse response to extract stage and explanation
    # In a real implementation, you would use structured output parsing
    stage_lines = response.content.split("\n")
    stage = None
    explanation = response.content
    
    for line in stage_lines:
        if line.startswith("Stage:"):
            stage = line.replace("Stage:", "").strip()
            break
    
    return {
        "stage": stage,
        "explanation": explanation,
        "messages": [user_message, response]
    }

def generate_report(state: CancerStagingState):
    """Generate final staging report"""
    llm = get_llm_with_system_prompt(
        system_prompt="""You are a pediatric oncology report specialist.
        You create clear, professional reports on cancer staging for medical records.
        Your reports are comprehensive yet concise, focusing on the most important clinical information.
        """
    )
    
    # Prepare user message
    user_message = HumanMessage(
        content=f"""Please generate a professional cancer staging report based on the following information:
        
        Cancer Type: {state.get('cancer_type', 'Unknown')}
        Standardized Category: {state.get('standardized_cancer_type', 'Unknown')}
        Stage: {state.get('stage', 'Unknown')}
        
        Staging Explanation:
        {state.get('explanation', 'No explanation provided')}
        
        Medical Note:
        {state['medical_note']}
        """
    )
    
    # Call the LLM to generate report
    response = llm([user_message])
    
    return {
        "report": response.content,
        "messages": [user_message, response]
    }

def should_proceed_to_staging(state: CancerStagingState):
    """Determine whether to proceed with staging or end with error"""
    if state.get("is_covered_by_toronto", False):
        return "analyze_criteria"
    else:
        return "generate_report"

def build_cancer_staging_graph():
    """Build and return the cancer staging graph"""
    # Initialize the workflow graph
    workflow = StateGraph(CancerStagingState)
    
    # Add nodes
    workflow.add_node("identify_cancer", identify_cancer_type)
    workflow.add_node("analyze_criteria", analyze_staging_criteria)
    workflow.add_node("calculate_stage", calculate_stage)
    workflow.add_node("generate_report", generate_report)
    
    # Connect edges
    workflow.add_edge(START, "identify_cancer")
    
    # Add conditional edge based on whether cancer is covered
    workflow.add_conditional_edges(
        "identify_cancer",
        should_proceed_to_staging,
        {
            "analyze_criteria": "analyze_criteria",
            "generate_report": "generate_report"
        }
    )
    
    workflow.add_edge("analyze_criteria", "calculate_stage")
    workflow.add_edge("calculate_stage", "generate_report")
    workflow.add_edge("generate_report", END)
    
    # Create a memory-based checkpointer
    memory = MemorySaver()
    
    # Compile the graph
    return workflow.compile(checkpointer=memory)

# Exported function to process a single note
def process_medical_note(note_text, thread_id="default", verbose=True):
    """
    Process a single medical note using the cancer staging graph.
    
    Args:
        note_text: The text of the medical note
        thread_id: Unique identifier for this run
        verbose: Whether to print verbose agent outputs
        
    Returns:
        Dict with the results including cancer type, stage, and report
    """
    logger.info(f"Processing medical note with thread_id: {thread_id}")
    
    # Build the graph
    graph = build_cancer_staging_graph()
    
    # Create initial state
    initial_state = {
        "messages": [],
        "medical_note": note_text,
    }
    
    # Run the graph with tracing of each step
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n" + "="*80)
    print("STARTING AGENT WORKFLOW - VERBOSE MODE")
    print("="*80)
    
    # We'll run the graph step by step to show outputs
    if verbose:
        # First step: identify cancer type
        print("\n🔍 STEP 1: CANCER IDENTIFICATION AGENT")
        print("-"*80)
        print("Agent prompt: Analyze this medical note and identify the cancer type")
        print("Medical note excerpt:", note_text[:300] + "..." if len(note_text) > 300 else note_text)
        print("-"*80)
        
        # Manually trigger the first node and get response
        step1_state = initial_state.copy()
        step1_result = identify_cancer_type(step1_state)
        
        # Extract and display the agent's response
        if "messages" in step1_result and len(step1_result["messages"]) > 1:
            agent_response = step1_result["messages"][-1].content
            print("\nAGENT RESPONSE:")
            print(agent_response)
            print("-"*80)
            print(f"Identified cancer type: {step1_result.get('cancer_type', 'Unknown')}")
            print(f"Standardized category: {step1_result.get('standardized_cancer_type', 'Unknown')}")
            print(f"Covered by Toronto: {'Yes' if step1_result.get('is_covered_by_toronto', False) else 'No'}")
        
        # Check if we should proceed to staging
        if step1_result.get("is_covered_by_toronto", False):
            # Second step: analyze staging criteria
            print("\n🔍 STEP 2: CRITERIA ANALYSIS AGENT")
            print("-"*80)
            
            # Update state with results from step 1
            step2_state = {**initial_state, **step1_result}
            
            # Get cancer type information for prompt
            cancer_type = step2_state.get("standardized_cancer_type") or step2_state.get("cancer_type", "Unknown")
            
            print(f"Agent prompt: Analyze medical note to identify staging criteria for {cancer_type}")
            print("-"*80)
            
            # Manually trigger the second node
            step2_result = analyze_staging_criteria(step2_state)
            
            # Extract and display the agent's response
            if "messages" in step2_result and len(step2_result["messages"]) > 1:
                agent_response = step2_result["messages"][-1].content
                print("\nAGENT RESPONSE:")
                print(agent_response)
                print("-"*80)
            
            # Third step: calculate stage
            print("\n🔍 STEP 3: STAGE CALCULATION AGENT")
            print("-"*80)
            
            # Update state with results from step 2
            step3_state = {**step2_state, **step2_result}
            
            print(f"Agent prompt: Calculate stage for {cancer_type} based on identified criteria")
            print("-"*80)
            
            # Manually trigger the third node
            step3_result = calculate_stage(step3_state)
            
            # Extract and display the agent's response
            if "messages" in step3_result and len(step3_result["messages"]) > 1:
                agent_response = step3_result["messages"][-1].content
                print("\nAGENT RESPONSE:")
                print(agent_response)
                print("-"*80)
                print(f"Determined stage: {step3_result.get('stage', 'Unknown')}")
            
            # Update state with results from step 3
            step4_state = {**step3_state, **step3_result}
        else:
            # Skip staging steps if cancer not covered
            step4_state = {**initial_state, **step1_result, 
                          "stage": "Not applicable", 
                          "explanation": "Cancer not covered by Toronto system"}
        
        # Fourth step: generate report
        print("\n🔍 STEP 4: REPORT GENERATION AGENT")
        print("-"*80)
        print("Agent prompt: Generate comprehensive staging report")
        print("-"*80)
        
        # Manually trigger the fourth node
        step4_result = generate_report(step4_state)
        
        # Extract and display the agent's response
        if "messages" in step4_result and len(step4_result["messages"]) > 1:
            agent_response = step4_result["messages"][-1].content
            print("\nAGENT RESPONSE:")
            print(agent_response)
            print("-"*80)
        
        # Combine all results
        final_result = {**step4_state, **step4_result}
        
    else:
        # Run the entire graph at once without verbose output
        final_result = graph.invoke(initial_state, config)
    
    print("\n" + "="*80)
    print("AGENT WORKFLOW COMPLETED")
    print("="*80)
    
    # Extract relevant information
    result_summary = {
        "cancer_type": final_result.get("cancer_type", "Unknown"),
        "standardized_cancer_type": final_result.get("standardized_cancer_type", "Unknown"),
        "stage": final_result.get("stage", "Unknown"),
        "extracted_stage": final_result.get("extracted_stage", "Not mentioned"),
        "primary_site": final_result.get("primary_site", "Not specified"),
        "metastasis_sites": final_result.get("metastasis_sites", "None identified"),
        "explanation": final_result.get("explanation", ""),
        "report": final_result.get("report", ""),
        "is_covered_by_toronto": final_result.get("is_covered_by_toronto", False),
        "medical_note": note_text
    }
    
    return result_summary 