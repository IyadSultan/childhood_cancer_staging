"""
Run the cancer staging module on the example medical note.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from src.staging_module import PediatricCancerStaging


# Load environment variables
load_dotenv()


# disable crewai telemetry from https://www.reddit.com/r/crewai/comments/1cp5gby/how_can_i_disable_all_telemetry_in_crewai/
from crewai.telemetry import Telemetry

def noop(*args, **kwargs):
    pass

def disable_crewai_telemetry():
    for attr in dir(Telemetry):
        if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
            setattr(Telemetry, attr, noop)



def main():
    """
    Run the cancer staging module on the example medical note.
    """
    disable_crewai_telemetry()

    parser = argparse.ArgumentParser(description="Run the cancer staging module on a medical note.")
    parser.add_argument("--use_original", action="store_true", help="Use the original Toronto staging data")
    parser.add_argument("--note", default="example.txt", help="Path to the medical note to process")
    parser.add_argument("--output", default="results.csv", help="Path to save the CSV results")
    args = parser.parse_args()
    
    # Set up OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key in the .env file.")
        sys.exit(1)
    
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Determine which staging data to use
    if args.use_original:
        staging_data_path = "toronoto_staging.json"
        print("Using original Toronto staging data")
    else:
        staging_data_path = "fixed_staging.json"
        print("Using fixed Toronto staging data")
    
    if not Path(staging_data_path).exists():
        print(f"Error: Staging data file not found at {staging_data_path}")
        print("Please make sure the staging data file is in the project root directory.")
        sys.exit(1)
    
    # Create the staging module
    staging_module = PediatricCancerStaging(
        staging_data_path=staging_data_path,
        model="gpt-4o-mini"
    )
    
    # Process the example medical note
    note_path = args.note
    output_path = args.output
    
    if not Path(note_path).exists():
        print(f"Error: Medical note not found at {note_path}")
        print("Please make sure the medical note file exists.")
        sys.exit(1)
    
    try:
        print(f"Processing medical note: {note_path}")
        staging_module.process_single_note(note_path, output_path)
        print(f"Results saved to: {output_path}")
        
        # Update project status
        status_file = Path("project_status.md")
        if status_file.exists():
            with open(status_file, "r", encoding="utf-8") as f:
                status_content = f.read()
            
            # Add a line about successful testing
            if "- Successfully tested the module on example medical notes" not in status_content:
                status_content = status_content.replace(
                    "## Current Status",
                    "## Current Status\n- Successfully tested the module on example medical notes"
                )
                
                with open(status_file, "w", encoding="utf-8") as f:
                    f.write(status_content)
                
                print("Project status updated.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 