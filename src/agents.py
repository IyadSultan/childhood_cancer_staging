from crewai import Agent
from typing import Dict, Any, List, Optional

class CancerStagingAgents:
    """
    Provides agents for pediatric cancer staging tasks.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the agent creator with the specified model.
        
        Args:
            model (str): The OpenAI model to use
        """
        self.model = model
    
    def create_cancer_identifier_agent(self) -> Agent:
        """
        Creates an agent specialized in identifying cancer types and extracting
        EMR stages from medical notes.
        
        Returns:
            Agent: A CrewAI agent for cancer identification
        """
        return Agent(
            role="Pediatric Oncology Specialist",
            goal="Identify the pediatric cancer type and any mentioned EMR stage in medical notes",
            backstory="""You are a specialist in pediatric oncology with extensive experience
            in diagnosing various childhood cancers. Your expertise allows you to quickly 
            identify cancer types from medical notes and extract any staging information 
            that may be mentioned.""",
            verbose=True,
            allow_delegation=False,
            llm_config={"model": self.model}
        )
    
    def create_criteria_analyzer_agent(self) -> Agent:
        """
        Creates an agent specialized in identifying staging criteria for a specific cancer type.
        
        Returns:
            Agent: A CrewAI agent for staging criteria analysis
        """
        return Agent(
            role="Cancer Staging Specialist",
            goal="Identify which staging criteria are present in the medical notes for a specific cancer type",
            backstory="""You are a specialist in pediatric cancer staging with deep knowledge
            of the Toronto staging system. Your expertise allows you to meticulously analyze
            medical notes and identify which specific staging criteria are present for a
            particular cancer type.""",
            verbose=True,
            allow_delegation=False,
            llm_config={"model": self.model}
        )
    
    def create_stage_calculator_agent(self) -> Agent:
        """
        Creates an agent specialized in calculating the Toronto stage based on criteria.
        
        Returns:
            Agent: A CrewAI agent for stage calculation
        """
        return Agent(
            role="Pediatric Cancer Stage Calculator",
            goal="Calculate the Toronto stage based on identified criteria",
            backstory="""You are an expert in applying the Toronto staging system for 
            childhood cancers. Your deep understanding of the staging system allows you
            to accurately determine the stage based on the criteria present in the
            medical notes.""",
            verbose=True,
            allow_delegation=False,
            llm_config={"model": self.model}
        )
    
    def create_report_generator_agent(self) -> Agent:
        """
        Creates an agent specialized in generating explanations for the staging.
        
        Returns:
            Agent: A CrewAI agent for explanation generation
        """
        return Agent(
            role="Medical Report Specialist",
            goal="Generate clear explanations for cancer staging decisions",
            backstory="""You are a medical report specialist with expertise in 
            explaining complex medical decisions. You can clearly articulate the
            reasoning behind cancer staging determinations in a way that is both
            accurate and comprehensible.""",
            verbose=True,
            allow_delegation=False,
            llm_config={"model": self.model}
        ) 