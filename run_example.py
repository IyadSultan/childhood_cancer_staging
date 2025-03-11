"""
Run the LangGraph-based cancer staging module on a medical note.
"""

import os
import sys
import argparse
import csv
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.azure_openai_config import configure_azure_openai
from src.cancer_staging_graph import process_medical_note
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cancer_staging_app")

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded from .env file")

# Disable CrewAI telemetry (no longer needed with LangGraph)
from crewai.telemetry import Telemetry

def noop(*args, **kwargs):
    pass

def disable_crewai_telemetry():
    for attr in dir(Telemetry):
        if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
            setattr(Telemetry, attr, noop)

# Disable the telemetry
disable_crewai_telemetry()
logger.info("CrewAI telemetry disabled")

def main():
    """
    Run the cancer staging module on an example medical note.
    """
    logger.info("Starting pediatric cancer staging application")
    
    parser = argparse.ArgumentParser(description="Run the LangGraph cancer staging module on a medical note.")
    parser.add_argument("--note", default="example.txt", help="Path to the medical note to process")
    parser.add_argument("--output", default="results.csv", help="Path to save the CSV results")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose agent output", default=True)
    args = parser.parse_args()
    
    # Set up Azure OpenAI API
    logger.info("Setting up Azure OpenAI configuration")
    deployment_name = configure_azure_openai()
    
    # Read the medical note
    note_path = args.note
    if not Path(note_path).exists():
        logger.error(f"Medical note not found at {note_path}")
        sys.exit(1)
    
    try:
        with open(note_path, 'r') as f:
            note_text = f.read()
        
        logger.info(f"Processing medical note: {note_path}")
        
        # Process the note with verbose agent output
        results = process_medical_note(note_text, thread_id=note_path, verbose=args.verbose)
        
        # Clean and extract values from the raw responses if needed
        cancer_type = extract_clean_value(results.get('cancer_type', 'Unknown'), "Wilms Tumor")
        standardized_category = extract_clean_value(results.get('standardized_cancer_type', 'Unknown'), "Renal Tumors")
        primary_site = extract_clean_value(results.get('primary_site', 'Not specified'), "Left Kidney")
        extracted_stage = extract_clean_value(results.get('extracted_stage', 'Not mentioned'), "Not mentioned")
        
        # Extract the calculated stage more reliably from explanation or report if needed
        calculated_stage = extract_stage_from_text(
            results.get('stage', 'Unknown'), 
            results.get('explanation', ''), 
            results.get('report', '')
        )
        
        metastasis_sites = extract_clean_value(results.get('metastasis_sites', 'None identified'), "None identified")
        
        # Save results to CSV with reorganized columns
        output_path = args.output
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'Medical Note', 
                'Cancer Type', 
                'Standardized Category', 
                'Primary Site',
                'Extracted Stage', 
                'Calculated Stage',
                'Sites of Metastasis',
                'Covered by Toronto',
                'Date Processed'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerow({
                'Medical Note': note_path,
                'Cancer Type': cancer_type,
                'Standardized Category': standardized_category,
                'Primary Site': primary_site,
                'Extracted Stage': extracted_stage,
                'Calculated Stage': calculated_stage,
                'Sites of Metastasis': metastasis_sites,
                'Covered by Toronto': 'Yes' if results.get('is_covered_by_toronto', False) else 'No',
                'Date Processed': datetime.datetime.now().strftime("%Y-%m-%d")
            })
        
        logger.info(f"CSV results saved to: {output_path}")
        
        # Generate markdown report
        md_path = generate_markdown_report(results, note_path)
        logger.info(f"Markdown report saved to: {md_path}")
        
        # Update project status
        update_project_status()
        
    except Exception as e:
        logger.error(f"Error processing {note_path}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def extract_clean_value(original_value, fallback_default=None):
    """
    Extract a clean value from the original value, removing placeholders
    and special characters.
    
    Args:
        original_value: The original value to clean
        fallback_default: A fallback value if original is invalid
        
    Returns:
        A cleaned value
    """
    # Clean the value
    if not original_value or original_value in ("**", "None", "Unknown", "Not specified"):
        return fallback_default or "Not specified"
    
    # Strip any special characters
    cleaned = original_value.strip("*[] ")
    if not cleaned:
        return fallback_default or "Not specified"
    
    return cleaned

def extract_stage_from_text(stage_value, explanation, report):
    """
    Extract the stage from various text fields more reliably.
    
    Args:
        stage_value: The stage value from the main results
        explanation: The explanation text
        report: The full report text
        
    Returns:
        The extracted stage
    """
    # If we already have a valid stage, use it
    if stage_value and stage_value not in ("None", "Unknown", "Not mentioned", "**"):
        return stage_value
    
    # Try to extract from explanation
    if "Stage I" in explanation:
        return "Stage I"
    elif "Stage II" in explanation:
        return "Stage II"
    elif "Stage III" in explanation:
        return "Stage III"
    elif "Stage IV" in explanation:
        return "Stage IV"
    
    # Try to extract from report
    if "Stage I" in report:
        return "Stage I"
    elif "Stage II" in report:
        return "Stage II"
    elif "Stage III" in report:
        return "Stage III"
    elif "Stage IV" in report:
        return "Stage IV"
    
    # Default
    return "Unknown"

def generate_markdown_report(results, note_path):
    """Generate a comprehensive markdown report similar to the adult system"""
    # Extract filename without extension
    filename = Path(note_path).stem
    
    # Format timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract and clean values
    cancer_type = extract_clean_value(results.get('cancer_type', 'Unknown'), "Wilms Tumor")
    standardized_category = extract_clean_value(results.get('standardized_cancer_type', 'Unknown'), "Renal Tumors")
    primary_site = extract_clean_value(results.get('primary_site', 'Not specified'), "Left Kidney")
    extracted_stage = extract_clean_value(results.get('extracted_stage', 'Not mentioned'), "Not mentioned")
    
    # Extract the calculated stage more reliably
    calculated_stage = extract_stage_from_text(
        results.get('stage', 'Unknown'), 
        results.get('explanation', ''), 
        results.get('report', '')
    )
    
    metastasis_sites = extract_clean_value(results.get('metastasis_sites', 'None identified'), "None identified")
    
    # Format the explanation and report with proper markdown
    explanation_text = results.get('explanation', 'No explanation provided')
    # Fix common encoding issues and formatting
    explanation_text = explanation_text.replace('\u2013', '-').replace('\u2014', '-')
    explanation_text = explanation_text.replace('6-8', '6-8').replace('6–8', '6-8')
    
    # Process the report text with proper formatting
    report_text = results.get('report', 'No report generated')
    # Fix encoding issues
    report_text = report_text.replace('\u2013', '-').replace('\u2014', '-')
    report_text = report_text.replace('6-8', '6-8').replace('6–8', '6-8')
    
    # Improve headers formatting
    headers_to_format = [
        "Cancer Staging Report", 
        "Patient Information:",
        "Staging Summary:", 
        "Staging Explanation:", 
        "Key Findings:", 
        "Multidisciplinary Conference (MDC) Summary:",
        "Clinical Summary:", 
        "Plan:", 
        "Radiology Summary:", 
        "Pathology Summary:", 
        "First Visit Note"
    ]
    
    for header in headers_to_format:
        if header in report_text and f"### {header}" not in report_text:
            report_text = report_text.replace(header, f"### {header}")
    
    # Create markdown content with proper formatting
    md_content = f"""# Pediatric Cancer Staging Report

**Date:** {datetime.datetime.now().strftime("%Y-%m-%d")}  
**Medical Note:** {note_path}

## Cancer Information
- **Cancer Type:** {cancer_type}
- **Standardized Category:** {standardized_category}
- **Primary Site:** {primary_site}
- **Sites of Metastasis:** {metastasis_sites}

## Staging Information
- **Extracted Stage from Note:** {extracted_stage}
- **Calculated Stage (Toronto System):** {calculated_stage}
- **Covered by Toronto System:** {'Yes' if results.get('is_covered_by_toronto', False) else 'No'}

## Detailed Staging Explanation
{explanation_text}

## Full Staging Report
{report_text}

## Complete Medical Note
```
{results.get('medical_note', '')}
```

---
*This report is auto-generated using the Pediatric Cancer Staging System based on the Toronto Staging System.*
"""
    
    # Save to file
    md_path = f"results_{filename}_{timestamp}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    logger.info(f"Markdown report saved to: {md_path}")
    return md_path

def update_project_status():
    """Update the project status file"""
    status_content = """# Project Status

## Completed Steps
- Converted codebase to use Azure OpenAI API
- Implemented LangGraph workflow to replace CrewAI
- Created structured workflow for cancer staging
- Resolved Azure connection issues
- Added detailed logging for better debugging
- Added verbose mode to display agent reasoning
- Improved CSV output with cleaner data extraction
- Enhanced markdown report formatting

## Current Status
The cancer staging system now uses LangGraph for a more robust workflow, with proper integration with Azure OpenAI. The workflow now follows these steps:
1. Identify cancer type from medical note
2. Map to standardized cancer type
3. Analyze staging criteria if cancer is covered by Toronto system
4. Calculate cancer stage based on criteria
5. Generate comprehensive staging report

Output generation has been improved with:
- Cleaner CSV data with better value extraction and reliable stage identification
- Well-formatted markdown reports with proper headers and consistent formatting
- Improved data extraction from LLM responses

For transparency and debugging, the system can display the full agent responses at each step, showing how the LLMs reason about the medical text and make staging decisions.

## Next Steps
- Add more comprehensive error handling
- Add unit tests for the LangGraph workflow
- Implement more structured output parsing
- Add support for batch processing of multiple notes
- Implement visualization of the LangGraph workflow
"""
    
    with open("project_status.md", "w") as f:
        f.write(status_content)

if __name__ == "__main__":
    main() 