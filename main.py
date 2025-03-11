import os
import argparse
import sys
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



def setup_openai_api():
    """
    Set up the Azure OpenAI API credentials from environment variables.
    """
    api_key = os.getenv("AZURE_API_KEY")
    endpoint = os.getenv("AZURE_ENDPOINT")
    api_version = os.getenv("AZURE_API_VERSION")
    
    if not api_key:
        print("Error: AZURE_API_KEY environment variable not set.")
        sys.exit(1)
    
    if not endpoint:
        print("Error: AZURE_ENDPOINT environment variable not set.")
        sys.exit(1)
    
    if not api_version:
        print("Error: AZURE_API_VERSION environment variable not set.")
        sys.exit(1)
    
    # Set environment variables for Azure OpenAI
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint
    os.environ["AZURE_OPENAI_API_VERSION"] = api_version

def create_project_status(results_path):
    """
    Create or update the project_status.md file.
    """
    status_file = Path("project_status.md")
    
    if results_path.exists():
        status_content = f"""# Pediatric Cancer Staging Project Status

## Completed Steps
- Created cancer staging module with CrewAI agents
- Processed medical notes and extracted cancer type and staging information
- Applied Toronto staging system to medical notes
- Generated staging reports with explanations
- Saved results to CSV file at: {results_path}

## Current Status
- The staging module has successfully processed the provided medical notes
- Results are available in the CSV file

## Next Steps
- Evaluate staging accuracy with clinical experts
- Extend the module to handle more complex medical notes
- Improve error handling and robustness
- Develop a user interface for easier interaction

"""
    else:
        status_content = f"""# Pediatric Cancer Staging Project Status

## Completed Steps
- Created cancer staging module with CrewAI agents
- Attempted to process medical notes but encountered errors

## Current Status
- The staging module encountered issues during processing
- Results were not generated successfully

## Next Steps
- Debug the staging module
- Fix the identified issues
- Retry processing the medical notes

"""
    
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(status_content)
    
    print(f"Project status updated in {status_file}")

def main():
    """
    Main function to run the cancer staging module.
    """
    disable_crewai_telemetry()

    parser = argparse.ArgumentParser(description="Process medical notes for pediatric cancer staging.")
    parser.add_argument("--note", help="Path to a single medical note to process")
    parser.add_argument("--staging_data", default="toronto_staging.json", help="Path to the Toronto staging data JSON file")
    parser.add_argument("--output", default="results.csv", help="Path to save the CSV results")
    parser.add_argument("--model", default="gpt-4o-mini", help="Azure OpenAI model deployment name to use")
    
    args = parser.parse_args()
    
    # Set up Azure OpenAI API
    setup_openai_api()
    
    # Check if staging data file exists
    staging_data_path = Path(args.staging_data)
    if not staging_data_path.exists():
        print(f"Error: Staging data file not found at {staging_data_path}")
        sys.exit(1)
    
    # Create the staging module
    staging_module = PediatricCancerStaging(
        staging_data_path=str(staging_data_path),
        model=args.model
    )
    
    # Process the medical note
    note_path = args.note if args.note else "example.txt"
    output_path = Path(args.output)
    
    if not Path(note_path).exists():
        print(f"Error: Medical note file not found at {note_path}")
        sys.exit(1)
    
    try:
        print(f"Processing medical note: {note_path}")
        staging_module.process_single_note(note_path, str(output_path))
        print(f"Results saved to: {output_path}")
        create_project_status(output_path)
    except Exception as e:
        print(f"Error: {e}")
        create_project_status(Path("error"))
        sys.exit(1)

if __name__ == "__main__":
    main() 