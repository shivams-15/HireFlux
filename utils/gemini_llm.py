"""
Gemini LLM Wrapper for CrewAI Integration
==========================================

This module provides a wrapper for Google's Gemini API to work with CrewAI.
It includes both the LangChain integration and a direct client interface.
"""

import os
import logging
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class GeminiClient:
    """Direct Gemini API client for non-CrewAI usage"""
    
    def __init__(self, model: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        """
        Initialize Gemini client
        
        Args:
            model: Gemini model name (gemini-pro, gemini-1.5-pro, gemini-1.5-flash)
            api_key: Gemini API key (optional, defaults to GEMINI_API_KEY env var)
        """
        self.model_name = model
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Gemini client with model: {self.model_name}")
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content using Gemini
        
        Args:
            prompt: Text prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        try:
            response = self.model.generate_content(prompt, **kwargs)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with Gemini: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Chat with Gemini using message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response text
        """
        try:
            # Start chat session
            chat = self.model.start_chat(history=[])
            
            # Process messages
            for msg in messages[:-1]:  # All but last message
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Send last message and get response
            if messages:
                last_msg = messages[-1]
                if last_msg['role'] == 'user':
                    response = chat.send_message(last_msg['content'], **kwargs)
                    return response.text
            
            return ""
        except Exception as e:
            logger.error(f"Error in Gemini chat: {e}")
            raise


def get_gemini_llm(model: str = "gemini-1.5-flash", temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """
    Get LangChain-compatible Gemini LLM for CrewAI
    
    Args:
        model: Gemini model name
        temperature: Temperature for generation (0.0 to 1.0)
        
    Returns:
        ChatGoogleGenerativeAI instance configured for CrewAI
    """
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in environment variables. "
            "Get your API key from https://makersuite.google.com/app/apikey"
        )
    
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        convert_system_message_to_human=True  # Gemini doesn't support system messages
    )
    
    logger.info(f"Created LangChain Gemini LLM with model: {model}")
    return llm


# Model name mapping for compatibility (Updated May 2026)
MODEL_MAPPING = {
    # OpenAI to Gemini mapping (use latest stable equivalents)
    "gpt-4o-mini": "gemini-3.5-flash",
    "gpt-4-turbo-preview": "gemini-2.5-pro",
    "gpt-3.5-turbo": "gemini-3.1-flash-lite",
    "gpt-4": "gemini-2.5-pro",
    "gpt-4o": "gemini-3.5-flash",
    
    # Gemini 3.x series (Latest - May 2026)
    "gemini-3.5-flash": "gemini-3.5-flash",  # Most intelligent stable
    "gemini-3.1-flash-lite": "gemini-3.1-flash-lite",  # Budget stable
    "gemini-3-flash-preview": "gemini-3-flash-preview",  # Frontier preview
    "gemini-3.1-pro-preview": "gemini-3.1-pro-preview",  # Advanced preview
    
    # Gemini 2.5 series (Current stable generation)
    "gemini-2.5-flash": "gemini-2.5-flash",  # Proven workhorse
    "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",  # Budget option
    "gemini-2.5-pro": "gemini-2.5-pro",  # Most capable
    
    # Gemini 1.5 series (Previous generation - still supported)
    "gemini-1.5-pro": "gemini-1.5-pro",
    "gemini-1.5-flash": "gemini-1.5-flash",
    "gemini-pro": "gemini-2.5-flash",  # Redirect legacy to current
    
    # Deprecated models (redirect to stable alternatives)
    "gemini-2.0-flash": "gemini-3.5-flash",  # DEPRECATED - redirect
    "gemini-2.0-flash-exp": "gemini-3.5-flash",  # DEPRECATED - redirect
    "gemini-2.0-flash-lite": "gemini-3.1-flash-lite",  # DEPRECATED - redirect
}


def map_model_name(openai_model: str) -> str:
    """
    Map OpenAI model names to Gemini equivalents
    
    Args:
        openai_model: OpenAI model name or any Gemini model name
        
    Returns:
        Equivalent Gemini model name (defaults to gemini-3.5-flash)
    """
    return MODEL_MAPPING.get(openai_model, "gemini-3.5-flash")
