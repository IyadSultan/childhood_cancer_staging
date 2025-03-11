"""
Configuration module for Azure OpenAI integration with LangGraph.
"""

import os
import sys
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

def configure_azure_openai():
    """
    Configure environment variables for Azure OpenAI.
    This must be called before any LangGraph operations.
    Returns the deployment name for use in the workflow.
    """
    # Get Azure OpenAI settings from environment variables
    api_key = os.getenv("AZURE_API_KEY")
    api_version = os.getenv("AZURE_API_VERSION")
    endpoint = os.getenv("AZURE_ENDPOINT")
    deployment_name = os.getenv("AZURE_GPT4O_DEPLOYMENT", "gpt-4o-mini")
    
    # Validate required environment variables
    if not api_key or not endpoint or not api_version:
        print("Error: Required Azure OpenAI environment variables not set.")
        print("Please ensure AZURE_API_KEY, AZURE_ENDPOINT, and AZURE_API_VERSION are set.")
        sys.exit(1)
    
    # Set OpenAI environment variables for LangGraph/LangChain
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_API_BASE"] = endpoint
    os.environ["OPENAI_API_VERSION"] = api_version
    os.environ["OPENAI_API_TYPE"] = "azure"
    
    # Also set Azure OpenAI specific variables
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint
    os.environ["AZURE_OPENAI_API_VERSION"] = api_version
    
    # Print configuration (with redacted API key)
    print(f"Azure OpenAI configured with:")
    print(f"  Endpoint: {endpoint}")
    print(f"  API Version: {api_version}")
    print(f"  Deployment: {deployment_name}")
    
    return deployment_name

def get_azure_openai_llm(deployment_name=None, temperature=0.3):
    """
    Get a configured AzureChatOpenAI instance for use with LangChain.
    
    Args:
        deployment_name: Override the deployment name from environment variable
        temperature: Temperature setting for the LLM
        
    Returns:
        AzureChatOpenAI: Configured LangChain LLM
    """
    if not deployment_name:
        deployment_name = os.getenv("AZURE_GPT4O_DEPLOYMENT", "gpt-4o-mini")
    
    api_key = os.getenv("AZURE_API_KEY")
    api_version = os.getenv("AZURE_API_VERSION")
    endpoint = os.getenv("AZURE_ENDPOINT")
    
    # Create and return the LLM
    return AzureChatOpenAI(
        deployment_name=deployment_name,
        openai_api_version=api_version,
        openai_api_key=api_key,
        azure_endpoint=endpoint,
        temperature=temperature
    )

def get_llm_with_system_prompt(system_prompt, deployment_name=None, temperature=0.3):
    """
    Get an LLM with a system prompt already applied.
    
    Args:
        system_prompt: The system prompt to apply
        deployment_name: Override the deployment name
        temperature: Temperature setting for the LLM
        
    Returns:
        A callable LLM function with the system prompt applied
    """
    llm = get_azure_openai_llm(deployment_name, temperature)
    
    def invoke_with_system(messages):
        # Add system message at the beginning if not already present
        if not (messages and messages[0].type == "system"):
            messages = [SystemMessage(content=system_prompt)] + messages
        return llm.invoke(messages)
    
    return invoke_with_system 