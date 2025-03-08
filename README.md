# Pediatric Cancer Staging Module

This module analyzes medical notes to identify cancer types and determine appropriate staging using the Toronto staging system for pediatric cancers.

## Features

- Identifies the cancer type from medical notes
- Extracts EMR stage if mentioned in the notes
- Analyzes clinical criteria for staging based on the Toronto system
- Calculates the appropriate stage based on identified criteria
- Generates explanations for staging decisions
- Outputs results to CSV files

## Requirements

- Python 3.8+
- OpenAI API key
- Required packages (see requirements.txt)

## Installation

1. Clone this repository
2. Create a virtual environment (if not already created):
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```
4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
5. Set up your OpenAI API key as an environment variable:
   ```
   # Windows
   set OPENAI_API_KEY=your_api_key_here
   
   # Linux/Mac
   export OPENAI_API_KEY=your_api_key_here
   ```
   Alternatively, create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Using the Example Script

The easiest way to use the module is with the provided example script:

```
# Use the fixed staging data (recommended)
python run_example.py

# Use the original staging data
python run_example.py --use_original

# Process a different medical note
python run_example.py --note path/to/medical_note.txt --output results.csv
```

### Using the Main Script

For more options, you can use the main script:

```
python main.py --note path/to/medical_note.txt --output results.csv --staging_data path/to/staging_data.json
```

### Command-line Arguments

#### run_example.py
- `--use_original`: Use the original Toronto staging data (default: use fixed_staging.json)
- `--note`: Path to the medical note to process (default: example.txt)
- `--output`: Path to save the CSV results (default: results.csv)

#### main.py
- `--note`: Path to the medical note to process (default: example.txt)
- `--staging_data`: Path to the Toronto staging JSON file (default: toronoto_staging.json)
- `--output`: Path to save the CSV results (default: results.csv)
- `--model`: OpenAI model to use (default: gpt-4o-mini)

## Staging Data

The module uses the Toronto staging system for pediatric cancers:

- **Original Data**: `toronoto_staging.json` contains the original staging information for all supported cancer types, but with some JSON syntax issues
- **Fixed Data**: `fixed_staging.json` contains the same information with corrected JSON syntax

The module will attempt to use the specified staging data file first. If there are issues parsing it, it will try to automatically fix the JSON errors. If that fails, it will fall back to a fixed version of the file if available. As a last resort, it will use a minimal staging dataset for Wilms Tumor only.

## Output Format

The module produces a CSV file with the following columns:

- `file_name`: Name of the processed medical note file
- `emr_stage`: Stage mentioned in the medical note (if any)
- `calculated_stage`: Stage calculated based on the Toronto staging system
- `explanation`: Explanation for the calculated stage

## Project Structure

```
.
├── main.py                  # Main script to run the module
├── run_example.py           # Simplified script for easy testing
├── requirements.txt         # Required packages
├── README.md                # This file
├── project_status.md        # Current project status
├── example.txt              # Example medical note
├── toronoto_staging.json    # Original Toronto staging system data
├── fixed_staging.json       # Fixed Toronto staging system data
├── .env.example             # Example environment file
└── src/                     # Source code
    ├── __init__.py          # Package initialization
    ├── agents.py            # Agent definitions
    ├── tasks.py             # Task definitions
    └── staging_module.py    # Main staging module
```

## How It Works

The module uses a series of AI agents, implemented with the CrewAI framework, to process medical notes:

1. **Cancer Identifier Agent**: Identifies the cancer type and any EMR stage mentioned
2. **Criteria Analyzer Agent**: Identifies which staging criteria are present in the notes
3. **Stage Calculator Agent**: Calculates the appropriate stage based on identified criteria
4. **Report Generator Agent**: Generates explanations for staging decisions

Each agent performs a specific task in the staging workflow, working together to produce accurate staging results.

## Supported Cancer Types

The module supports staging for all pediatric cancers in the Toronto staging system, including:

- Acute Lymphoblastic Leukemia
- Hodgkin Lymphoma
- Non-Hodgkin Lymphoma
- Neuroblastoma
- Wilms Tumor (Renal Tumors)
- Rhabdomyosarcoma
- Non-Rhabdo Soft Tissue Sarcoma
- Bone Tumors
- Retinoblastoma
- Hepatoblastoma
- Testicular Germ Cell Tumor
- Ovarian Germ Cell Tumor
- Astrocytoma
- Medulloblastoma (CNS Embryonal Tumors)
- Ependymoma

## License

MIT 