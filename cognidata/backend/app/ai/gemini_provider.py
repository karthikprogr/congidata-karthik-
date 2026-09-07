"""
Gemini AI Provider for Cognidata
Implements Requirements: 5.1, 5.2, 5.3, 5.4, 13.1, 13.2
"""
import google.generativeai as genai
from typing import Optional, Dict, Any
import asyncio
from functools import wraps
from app.core.config import GEMINI_API_KEY

def async_retry(max_retries=3, delay=1.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = delay * (2 ** attempt)
                    print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
        return wrapper
    return decorator

class GeminiProvider:
    """
    Google Gemini API Provider
    Supports gemini-3.6-flash (default) and gemini-3.6-pro (complex reasoning)
    """
    
    def __init__(self, model: str = "gemini-3.6-flash"):
        """
        Initialize Gemini provider
        
        Args:
            model: Model name (gemini-3.6-flash or gemini-3.6-pro)
        """
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
    
    @async_retry(max_retries=3, delay=1.0)
    async def generate_text(
        self, 
        prompt: str, 
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using Gemini
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Generated text string
        """
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature
                    )
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API Error: {str(e)}")
    
    async def generate_with_context(
        self,
        messages: list,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text with conversation context
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text string
        """
        # Convert messages to single prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        full_prompt = "\n\n".join(prompt_parts)
        return await self.generate_text(full_prompt, max_tokens, temperature)
    
    def get_token_count(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 chars per token
        return len(text) // 4
    
    @staticmethod
    def list_available_models() -> list:
        """List all available Gemini models"""
        genai.configure(api_key=GEMINI_API_KEY)
        models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                models.append(m.name)
        return models


# Convenience instances
gemini_flash = GeminiProvider("gemini-3.6-flash")  # Fast, default - optimized for <2s response time
gemini_pro = GeminiProvider("gemini-3.6-pro")  # Complex reasoning
