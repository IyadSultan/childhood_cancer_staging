import json
import os
import csv
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from pathlib import Path
from crewai import Crew

from .agents import CancerStagingAgents
from .tasks import CancerStagingTasks

class PediatricCancerStaging:
    """
    A module for analyzing medical notes and determining pediatric cancer staging
    using the Toronto staging system.
    """
    
    def __init__(self, staging_data_path: str, model: str = "gpt-4o-mini"):
        """
        Initialize the staging module.
        
        Args:
            staging_data_path: Path to the Toronto staging JSON file
            model: The OpenAI model to use
        """
        self.model = model
        self.staging_data = self._load_staging_data(staging_data_path)
        self.agents = CancerStagingAgents(model=model)
        
    def _load_staging_data(self, staging_data_path: str) -> Dict[str, Any]:
        """
        Load the Toronto staging data from a JSON file.
        
        Args:
            staging_data_path: Path to the Toronto staging JSON file
            
        Returns:
            Dict: The staging data as a dictionary
        """
        try:
            with open(staging_data_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Load the JSON data
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                # Attempt to fix the JSON if there are still any issues
                content = self._fix_json_syntax(content)
                return json.loads(content)
                
        except Exception as e:
            print(f"Error loading staging data: {e}")
            raise
    
    def _fix_json_syntax(self, content: str) -> str:
        """
        Fix common JSON syntax errors in the content.
        
        Args:
            content: JSON content with potential syntax errors
            
        Returns:
            str: Fixed JSON content
        """
        # Fix missing commas after closing brackets
        known_issues = [
            ('"CNS3": "Definite CNS involvement:', '],', '],'),
            ('"Stage IV": "Disseminated (multifocal)', '],', '],'),
            ('"Stage IV": "Involvement of the central', '],', '],'),
            ('"Stage IV": "Metastatic disease present', '],', '],'),
            ('"Stage IV": "Distant metastatic disease', '],', '],'),
            ('"Stage IIIC": "Either regional nodal', '],', '],'),
            ('"M4": "Metastasis outside the central', '],', '],')
        ]
        
        for search_text, search_pattern, replace_pattern in known_issues:
            if search_text in content:
                pos = content.find(search_text)
                if pos > 0:
                    end_pos = content.find(search_pattern, pos)
                    if end_pos > 0:
                        content = content[:end_pos] + replace_pattern + content[end_pos + len(search_pattern):]
        
        # Remove trailing commas before closing brackets
        content = content.replace("},}", "}}")
        content = content.replace("},]", "}]")
        
        # Fix the ending of the file
        if content.strip().endswith("}}}"):
            content = content.rstrip() + "}"
            
        return content
    
    def _read_medical_note(self, note_path: str) -> str:
        """
        Read a medical note from a file.
        
        Args:
            note_path: Path to the medical note file
            
        Returns:
            str: The contents of the medical note
        """
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading medical note: {e}")
            raise
            
    def process_medical_note(self, note_path: str) -> Tuple[str, str, str, str]:
        """
        Process a medical note and determine the cancer staging.
        
        Args:
            note_path: Path to the medical note file
            
        Returns:
            Tuple: (file_name, emr_stage, calculated_stage, explanation)
        """
        # Read the medical note
        medical_note = self._read_medical_note(note_path)
        file_name = os.path.basename(note_path)
        
        # Create agents for the staging workflow
        identifier_agent = self.agents.create_cancer_identifier_agent()
        criteria_agent = self.agents.create_criteria_analyzer_agent()
        calculator_agent = self.agents.create_stage_calculator_agent()
        reporter_agent = self.agents.create_report_generator_agent()
        
        # Create tasks for the staging workflow
        identify_task = CancerStagingTasks.identify_cancer_type(
            identifier_agent, medical_note, self.staging_data
        )
        
        # Execute identification task
        crew = Crew(
            agents=[identifier_agent],
            tasks=[identify_task],
            verbose=True
        )
        
        result = crew.kickoff()
        identification_result = result.raw
        
        # Parse the identification results
        cancer_type_line = next((line for line in identification_result.split('\n') 
                               if line.startswith('Cancer Type:')), '')
        emr_stage_line = next((line for line in identification_result.split('\n') 
                             if line.startswith('EMR Stage:')), '')
        
        cancer_type = cancer_type_line.replace('Cancer Type:', '').strip() if cancer_type_line else 'Unknown'
        emr_stage = emr_stage_line.replace('EMR Stage:', '').strip() if emr_stage_line else 'Not provided'
        
        # Execute criteria analysis task
        criteria_task = CancerStagingTasks.analyze_staging_criteria(
            criteria_agent, medical_note, cancer_type, self.staging_data
        )
        
        crew = Crew(
            agents=[criteria_agent],
            tasks=[criteria_task],
            verbose=True
        )
        
        result = crew.kickoff()
        criteria_analysis = result.raw
        
        # Execute stage calculation task
        calculate_task = CancerStagingTasks.calculate_stage(
            calculator_agent, medical_note, cancer_type, criteria_analysis, self.staging_data
        )
        
        crew = Crew(
            agents=[calculator_agent],
            tasks=[calculate_task],
            verbose=True
        )
        
        result = crew.kickoff()
        calculation_result = result.raw
        
        # Parse the calculation results
        stage_line = next((line for line in calculation_result.split('\n') 
                          if line.startswith('Calculated Stage:')), '')
        calculated_stage = stage_line.replace('Calculated Stage:', '').strip() if stage_line else 'Unknown'
        
        # Get explanation by removing the "Calculated Stage" line
        explanation_lines = [line for line in calculation_result.split('\n') 
                           if not line.startswith('Calculated Stage:') and line.strip()]
        explanation = '\n'.join(explanation_lines).replace('Explanation:', '').strip()
        
        # Generate the final report
        report_task = CancerStagingTasks.generate_report(
            reporter_agent, medical_note, cancer_type, emr_stage, 
            criteria_analysis, calculated_stage, explanation
        )
        
        crew = Crew(
            agents=[reporter_agent],
            tasks=[report_task],
            verbose=True
        )
        
        result = crew.kickoff()
        report = result.raw
        
        # Extract the CSV line from the report
        csv_line = next((line for line in report.split('\n') 
                        if line.startswith(file_name)), '')
        
        if csv_line:
            parts = csv_line.split(',')
            if len(parts) >= 4:
                file_name = parts[0]
                emr_stage = parts[1]
                calculated_stage = parts[2]
                explanation = ','.join(parts[3:])  # Explanation might contain commas
        
        return file_name, emr_stage, calculated_stage, explanation
    
    def process_multiple_notes(self, note_dir: str, output_csv: str) -> None:
        """
        Process multiple medical notes and save the results to a CSV file.
        
        Args:
            note_dir: Directory containing medical notes
            output_csv: Path to save the CSV results
        """
        results = []
        
        # Get all text files in the directory
        note_files = [f for f in os.listdir(note_dir) if f.endswith('.txt')]
        
        for note_file in note_files:
            note_path = os.path.join(note_dir, note_file)
            print(f"Processing {note_file}...")
            
            try:
                file_name, emr_stage, calculated_stage, explanation = self.process_medical_note(note_path)
                results.append({
                    'file_name': file_name,
                    'emr_stage': emr_stage,
                    'calculated_stage': calculated_stage,
                    'explanation': explanation
                })
                print(f"Completed processing {note_file}")
            except Exception as e:
                print(f"Error processing {note_file}: {e}")
        
        # Save results to CSV
        if results:
            df = pd.DataFrame(results)
            df.to_csv(output_csv, index=False)
            print(f"Results saved to {output_csv}")
        else:
            print("No results to save.")
            
    def process_single_note(self, note_path: str, output_csv: str) -> None:
        """
        Process a single medical note and save the result to a CSV file.
        
        Args:
            note_path: Path to the medical note file
            output_csv: Path to save the CSV result
        """
        try:
            file_name, emr_stage, calculated_stage, explanation = self.process_medical_note(note_path)
            
            # Save result to CSV
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['file_name', 'emr_stage', 'calculated_stage', 'explanation'])
                writer.writerow([file_name, emr_stage, calculated_stage, explanation])
            
            print(f"Result saved to {output_csv}")
        except Exception as e:
            print(f"Error processing {note_path}: {e}") 