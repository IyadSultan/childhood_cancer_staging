from crewai import Task
from typing import Dict, Any

class CancerStagingTasks:
    """
    Provides tasks for pediatric cancer staging workflow.
    """
    
    @staticmethod
    def identify_cancer_type(agent, medical_note: str, staging_data: Dict[str, Any]) -> Task:
        """
        Creates a task to identify the cancer type and EMR stage from medical notes.
        
        Args:
            agent: The agent to assign this task to
            medical_note: The medical note content
            staging_data: Toronto staging system data
            
        Returns:
            Task: A CrewAI task for cancer identification
        """
        return Task(
            description=f"""
            Analyze the provided medical note carefully to identify which pediatric cancer type 
            from the Toronto staging system is applicable.
            
            If multiple cancer types are mentioned, select the one that appears to be the primary diagnosis.
            Also extract any EMR stage mentioned in the note. If no stage is mentioned, indicate 'Not provided'.
            
            Medical Note:
            {medical_note}
            
            Available Cancer Types in Toronto Staging System:
            {', '.join(staging_data.keys())}
            
            Your response should follow this format:
            Cancer Type: [Identified cancer type]
            EMR Stage: [Extracted stage or 'Not provided']
            """,
            expected_output="Identification of cancer type and EMR stage from medical note",
            agent=agent
        )
    
    @staticmethod
    def analyze_staging_criteria(agent, medical_note: str, cancer_type: str, staging_data: Dict[str, Any]) -> Task:
        """
        Creates a task to analyze which staging criteria are present for a specific cancer type.
        
        Args:
            agent: The agent to assign this task to
            medical_note: The medical note content
            cancer_type: The identified cancer type
            staging_data: Toronto staging system data
            
        Returns:
            Task: A CrewAI task for criteria analysis
        """
        # Get criteria and definitions for the specific cancer type
        criteria = staging_data.get(cancer_type, {}).get("criteria", [])
        definitions = staging_data.get(cancer_type, {}).get("definitions", {})
        
        return Task(
            description=f"""
            Carefully analyze the provided medical note to identify which staging criteria 
            for {cancer_type} are present.
            
            Medical Note:
            {medical_note}
            
            Criteria to check for {cancer_type}:
            {chr(10).join([f"- {criterion}" for criterion in criteria])}
            
            Definitions to consider:
            {chr(10).join([f"- {key}: {value}" for key, value in definitions.items()])}
            
            For each criterion, determine if it is:
            - Present: Clearly indicated in the medical note
            - Absent: Clearly indicated as not present in the medical note
            - Unknown: Not mentioned or unclear from the medical note
            
            Provide a summary that lists all the criteria and whether they are present, absent, or unknown.
            Also include any additional relevant information from the definitions that helps understand the staging.
            """,
            expected_output="Analysis of which staging criteria are present, absent, or unknown",
            agent=agent
        )
    
    @staticmethod
    def calculate_stage(agent, medical_note: str, cancer_type: str, criteria_analysis: str, staging_data: Dict[str, Any]) -> Task:
        """
        Creates a task to calculate the Toronto stage based on the criteria analysis.
        
        Args:
            agent: The agent to assign this task to
            medical_note: The medical note content
            cancer_type: The identified cancer type
            criteria_analysis: The results of the criteria analysis
            staging_data: Toronto staging system data
            
        Returns:
            Task: A CrewAI task for stage calculation
        """
        # Get stages for the specific cancer type
        stages = staging_data.get(cancer_type, {}).get("stages", {})
        
        return Task(
            description=f"""
            Based on the criteria analysis, calculate the Toronto stage for {cancer_type}.
            
            Medical Note:
            {medical_note}
            
            Criteria Analysis:
            {criteria_analysis}
            
            Stages for {cancer_type}:
            {chr(10).join([f"- {stage}: {description}" for stage, description in stages.items()])}
            
            If the information provided is not sufficient to determine a stage with confidence,
            state "Information not adequate" and explain what specific information is missing.
            
            Otherwise, determine the most appropriate stage and provide a clear explanation
            of how you arrived at this determination based on the criteria present.
            
            Your response should follow this format:
            Calculated Stage: [Stage or 'Information not adequate']
            Explanation: [Your explanation]
            """,
            expected_output="Calculated Toronto stage with explanation",
            agent=agent
        )
    
    @staticmethod
    def generate_report(agent, medical_note: str, cancer_type: str, emr_stage: str, 
                        criteria_analysis: str, calculated_stage: str, explanation: str) -> Task:
        """
        Creates a task to generate a comprehensive report explaining the staging decision.
        
        Args:
            agent: The agent to assign this task to
            medical_note: The medical note content
            cancer_type: The identified cancer type
            emr_stage: The EMR stage (if provided)
            criteria_analysis: The results of the criteria analysis
            calculated_stage: The calculated Toronto stage
            explanation: The explanation for the calculated stage
            
        Returns:
            Task: A CrewAI task for report generation
        """
        return Task(
            description=f"""
            Generate a comprehensive report summarizing the cancer type, EMR stage (if provided),
            criteria analysis, calculated Toronto stage, and explanation.
            
            Medical Note Excerpt (first 300 chars):
            {medical_note[:300]}...
            
            Cancer Type: {cancer_type}
            EMR Stage: {emr_stage}
            
            Criteria Analysis:
            {criteria_analysis}
            
            Calculated Stage: {calculated_stage}
            Stage Explanation: {explanation}
            
            Your report should be structured to include the following in a CSV-friendly format:
            file_name,emr_stage,calculated_stage,explanation
            
            The explanation should be concise but comprehensive, focusing on the key factors
            that determined the staging decision.
            """,
            expected_output="Comprehensive report in CSV-friendly format",
            agent=agent
        ) 