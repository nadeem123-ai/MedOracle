"""
BaseAgent — shared LLM setup and JSON-safe parsing for all agents.

Provides centralized LLM initialization, JSON parsing with error recovery,
and timing utilities for agent execution monitoring.

Rate limit handling: Catches 429 errors and returns safe fallback responses.
"""
from __future__ import annotations
import json
import re
import time
import os
import logging
from typing import Any, Callable, Dict, TypeVar
from functools import wraps

from langchain_groq import ChatGroq
from groq import RateLimitError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., Dict[str, Any]])


def is_rate_limited(error: Exception) -> bool:
    """
    Check if an error is a rate limit error (429).
    
    Args:
        error: Exception to check
        
    Returns:
        True if error is a rate limit error
    """
    error_str = str(error).lower()
    return (
        "429" in str(error) or
        "rate_limit" in error_str or
        "rate limit" in error_str or
        isinstance(error, RateLimitError) or
        "tokens per day" in error_str
    )



def _get_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0.1) -> ChatGroq:
    """
    Initialize and return a Groq-backed LLM client.
    
    Args:
        model: Model identifier (default: Llama 3.3 70B)
        temperature: Sampling temperature for response generation (0.0-1.0)
        
    Returns:
        ChatGroq instance configured with API key from environment
        
    Raises:
        ValueError: If GROQ_API_KEY environment variable is not set
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    return ChatGroq(model=model, temperature=temperature, groq_api_key=api_key)


def parse_json_response(text: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling markdown code fences and formatting issues.
    
    Attempts to extract valid JSON from common LLM response formats:
    - ```json ... ```
    - ``` ... ```
    - Raw JSON
    
    Args:
        text: Raw text response from LLM
        
    Returns:
        Parsed dictionary, or empty dict if parsing fails
    """
    try:
        # Remove markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        
        # Find first JSON object { ... }
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed: {e}. Text: {cleaned[:200]}")
                return {}
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
    
    return {}


def timed_run(fn: T) -> T:
    """
    Decorator that measures and appends elapsed_ms to the returned dict.
    
    Usage:
        @timed_run
        def my_agent(state):
            return {"result": "value"}  # Will have _elapsed_ms added
    
    Args:
        fn: Function returning a dict
        
    Returns:
        Wrapped function with timing capability
    """
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        t0 = time.time()
        try:
            result = fn(*args, **kwargs)
            if isinstance(result, dict):
                result["_elapsed_ms"] = int((time.time() - t0) * 1000)
            return result
        except Exception as e:
            logger.error(f"Error in {fn.__name__}: {e}", exc_info=True)
            raise
    return wrapper  # type: ignore
