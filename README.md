# Pediatric Cancer Staging Module

This module analyzes medical notes to identify cancer types and determine appropriate staging using the Toronto staging system for pediatric cancers.

## Features

- Identifies the cancer type from medical notes
- Extracts EMR stage if mentioned in the notes
- Analyzes clinical criteria for staging based on the Toronto system
- Calculates the appropriate stage based on identified criteria
- Generates explanations for staging decisions
- Outputs results to CSV and markdown files
- Supports Azure OpenAI API integration
- Uses LangGraph for the workflow orchestration

## Requirements

- Python 3.8+
- Azure OpenAI API access
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
5. Set up your Azure OpenAI API credentials as environment variables:
   ```
   # Windows
   set AZURE_OPENAI_API_KEY=your_api_key_here
   set AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
   set AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here
   set AZURE_OPENAI_API_VERSION=2023-05-15
   
   # Linux/Mac
   export AZURE_OPENAI_API_KEY=your_api_key_here
   export AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
   export AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here
   export AZURE_OPENAI_API_VERSION=2023-05-15
   ```
   Alternatively, create a `.env` file in the project root with:
   ```
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
   AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here
   AZURE_OPENAI_API_VERSION=2023-05-15
   ```

## Using Alternative LLM Providers

This codebase currently uses Azure OpenAI, but it can be easily adapted to use other LLM providers:

### Converting to OpenAI

To use standard OpenAI API instead of Azure:

1. Modify `src/azure_openai_config.py` to initialize standard OpenAI:
   ```python
   from langchain_openai import ChatOpenAI
   
   def configure_openai():
       """Configure standard OpenAI API"""
       api_key = os.getenv("OPENAI_API_KEY")
       model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
       
       # Set up standard ChatOpenAI
       return ChatOpenAI(
           model=model_name,
           temperature=0.0,
           openai_api_key=api_key
       )
   ```

2. Update your environment variables:
   ```
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL_NAME=gpt-4o-mini  # or your preferred model
   ```

### Using Anthropic, Cohere or Other Providers

LangChain supports many LLM providers. Here's how to modify for a different provider:

1. Install the relevant package:
   ```
   pip install langchain-anthropic  # for Anthropic
   pip install langchain-cohere     # for Cohere
   ```

2. Modify the configuration:
   ```python
   from langchain_anthropic import ChatAnthropic
   
   def configure_anthropic():
       """Configure Anthropic Claude"""
       api_key = os.getenv("ANTHROPIC_API_KEY")
       
       return ChatAnthropic(
           model="claude-3-opus-20240229",
           temperature=0.0,
           anthropic_api_key=api_key
       )
   ```

For more information on supported LLM providers, refer to the [LangChain documentation](https://python.langchain.com/docs/integrations/llms/).

## Usage

### Using the Example Script

The easiest way to use the module is with the provided example script:

```
# Process the example medical note
python run_example.py

# Process a different medical note
python run_example.py --note path/to/medical_note.txt --output results.csv

# With verbose output
python run_example.py --verbose
```

### Command-line Arguments

#### run_example.py
- `--note`: Path to the medical note to process (default: example.txt)
- `--output`: Path to save the CSV results (default: results.csv)
- `--verbose`: Enable verbose agent output (default: True)

## LangGraph Workflow

This project uses LangGraph for workflow orchestration. The workflow consists of the following steps:

1. Identify cancer type from medical note
2. Map to standardized cancer type
3. Analyze staging criteria if cancer is covered by Toronto system
4. Calculate cancer stage based on criteria
5. Generate comprehensive staging report

To learn more about LangGraph:
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph/)
- [LangGraph State Management](https://python.langchain.com/docs/langgraph/state/)
- [Advanced LangGraph Patterns](https://python.langchain.com/docs/langgraph/advanced_patterns/)

## Output Format

The module produces both a CSV file and a detailed markdown report:

### CSV Output
- `Medical Note`: Name of the processed medical note file
- `Cancer Type`: Identified cancer type
- `Standardized Category`: Standardized cancer category
- `Primary Site`: Primary site of the cancer
- `Extracted Stage`: Stage mentioned in the medical note (if any)
- `Calculated Stage`: Stage calculated based on the Toronto staging system
- `Sites of Metastasis`: Identified metastasis sites (if any)
- `Covered by Toronto`: Whether the cancer type is covered by the Toronto system
- `Date Processed`: Date when the note was processed

### Markdown Report
A comprehensive report that includes:
- Cancer information details
- Staging information
- Detailed staging explanation
- Full staging report
- The complete medical note

## Project Structure

```
.
├── main.py                     # Main script to run the module
├── run_example.py              # Simplified script for easy testing
├── requirements.txt            # Required packages
├── README.md                   # This file
├── project_status.md           # Current project status
├── example.txt                 # Example medical note
├── toronto_staging.json        # Toronto staging system data
├── .env                        # Environment variables
└── src/                        # Source code
    ├── __init__.py             # Package initialization
    ├── azure_openai_config.py  # Azure OpenAI configuration
    ├── cancer_staging_graph.py # LangGraph definition
    └── utils.py                # Utility functions
```

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