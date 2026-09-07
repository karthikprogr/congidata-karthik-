"""
LLM Agent  Gemini-powered intelligence layer.

Features:
- Uses Google Gemini (gemini-3.6-flash for optimal speed)
- Conversation memory (last 10 exchanges)
- Safe pandas code execution with rich stdlib access
- Smart chart type selection
- Compact data summaries (low token usage)
- Query classification and enhanced responses (Simple vs Complex)
"""
import os
import re
import numpy as np
import pandas as pd
from typing import Optional
import asyncio
from enum import Enum
import time
import logging
import functools

# -- Module logger -------------------------------------------------------------

logger = logging.getLogger(__name__)


# -- Query Type Enum -----------------------------------------------------------

class QueryType(Enum):
    """
    Classification of user queries for response formatting.
    
    SIMPLE: Single fact or comparison queries (e.g., "Which category sells more?")
            Response limited to 1 sentence.
    
    COMPLEX: Multi-metric, trend, or analysis queries (e.g., "What are the sales trends?")
             Response limited to 3 sentences.
    """
    SIMPLE = "simple"
    COMPLEX = "complex"


# -- Query Classification ------------------------------------------------------

def _format_dataset_context(df: pd.DataFrame) -> dict:
    """
    Format dataset information with proper record count rounding.
    
    Formats the dataset context for inclusion in prompts, applying specific
    rounding rules to record counts based on dataset size:
    - <100 records: Exact count (e.g., "47")
    - 100-999: Rounded to nearest 10 (e.g., 847 ? "~850")
    - 1,000-9,999: Rounded to nearest 100 (e.g., 3,421 ? "~3,400")
    - 10,000+: Rounded to nearest 1,000 (e.g., 12,847 ? "~13,000")
    
    Also extracts column information, separating numeric and categorical columns.
    
    Args:
        df: Dataset to format context for
    
    Returns:
        Dictionary containing:
        - record_count (int): Actual record count
        - record_count_formatted (str): Display format (exact or rounded with ~)
        - num_columns (int): Total number of columns
        - column_names (List[str]): All column names
        - numeric_columns (List[str]): Names of numeric columns
        - categorical_columns (List[str]): Names of categorical/object columns
    
    Examples:
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
        >>> ctx = _format_dataset_context(df)
        >>> ctx['record_count']
        3
        >>> ctx['record_count_formatted']
        '3'
        >>> ctx['numeric_columns']
        ['A']
        >>> ctx['categorical_columns']
        ['B']
    """
    record_count = len(df)
    
    # Format record count per requirements
    if record_count < 100:
        record_count_formatted = f"{record_count}"
    elif record_count < 1000:
        rounded = round(record_count, -1)  # Nearest 10
        record_count_formatted = f"~{rounded:,}"
    elif record_count < 10000:
        rounded = round(record_count, -2)  # Nearest 100
        record_count_formatted = f"~{rounded:,}"
    else:
        rounded = round(record_count, -3)  # Nearest 1000
        record_count_formatted = f"~{rounded:,}"
    
    # Extract numeric columns
    nums = df.select_dtypes(include=np.number)
    numeric_columns = list(nums.columns)
    
    # Extract categorical columns
    cats = df.select_dtypes(include="object")
    categorical_columns = list(cats.columns)
    
    return {
        "record_count": record_count,
        "record_count_formatted": record_count_formatted,
        "num_columns": len(df.columns),
        "column_names": list(df.columns),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
    }


def _classify_query(question: str) -> QueryType:
    """
    Classify user query as Simple or Complex for response formatting.
    
    Simple queries request single facts or comparisons (e.g., "Which category sells more?")
    and receive 1-sentence responses.
    
    Complex queries request multiple metrics, trends, or analysis (e.g., "What are the sales trends?")
    and receive up to 3-sentence responses.
    
    Classification Logic:
    - Complex if contains keywords: "trend", "pattern", "breakdown", "compare across",
      "over time", "analysis", "correlation", "distribution"
    - Complex if contains multiple question components (e.g., "what and why")
    - Simple if contains single comparison words: "which", "who", "what", "how many" without modifiers
    - Defaults to Simple for ambiguous cases
    
    Args:
        question: User's question text
    
    Returns:
        QueryType.SIMPLE or QueryType.COMPLEX
    
    Examples:
        >>> _classify_query("Which category sells more?")
        QueryType.SIMPLE
        
        >>> _classify_query("What are the sales trends over time?")
        QueryType.COMPLEX
        
        >>> _classify_query("Show me breakdown by region")
        QueryType.COMPLEX
    """
    q_lower = question.lower()
    
    # Complex indicators (higher priority)
    complex_keywords = [
        "trend", "pattern", "breakdown", "compare across",
        "over time", "analysis", "correlation", "distribution"
    ]
    
    if any(keyword in q_lower for keyword in complex_keywords):
        return QueryType.COMPLEX
    
    # Check for multiple question components
    # Detect " and " with question words on both sides
    if " and " in q_lower:
        question_words = ["what", "which", "how", "why", "where", "who", "when"]
        if any(word in q_lower for word in question_words):
            # Check if there are question-related words around the "and"
            parts = q_lower.split(" and ")
            if len(parts) >= 2:
                # If any part contains question words, likely multiple components
                has_question_before = any(word in parts[0] for word in question_words)
                has_question_after = any(word in " and ".join(parts[1:]) for word in question_words)
                if has_question_before and has_question_after:
                    return QueryType.COMPLEX
    
    # Simple indicators - single comparison words without modifiers
    simple_patterns = [
        r'\bwhich\b',   # "which" as standalone word
        r'\bwho\b',     # "who" as standalone word
        r'\bwhat is\b', # "what is" phrase
        r'\bhow many\b' # "how many" phrase
    ]
    
    if any(re.search(pattern, q_lower) for pattern in simple_patterns):
        return QueryType.SIMPLE
    
    # Default to simple for ambiguous cases
    return QueryType.SIMPLE


def _validate_response_format(response: str, query_type: QueryType) -> tuple[bool, str]:
    """
    Validate that generated response meets format requirements.
    
    Performs soft validation checks on LLM-generated responses to ensure they
    meet conciseness, tone, and contextualization requirements. Validation
    failures are logged as warnings but do not block response delivery.
    
    Validation Rules:
    1. Sentence count: =1 for SIMPLE, =3 for COMPLEX
    2. No preambles: Response should not start with explanatory phrases
    3. Dataset reference: Must include record count OR possessive OR column name
    4. No technical jargon (for COMPLEX): Avoid statistical terms
    5. No academic transitions: Avoid formal academic writing conventions
    
    Args:
        response: Generated response text to validate
        query_type: Query complexity classification (SIMPLE or COMPLEX)
    
    Returns:
        Tuple of (is_valid, error_message):
        - is_valid (bool): True if all validation checks pass
        - error_message (str): Description of validation failure, empty if valid
    
    Examples:
        >>> _validate_response_format("Technology sells more in your 847 records.", QueryType.SIMPLE)
        (True, "")
        
        >>> _validate_response_format("Based on the data, Technology leads.", QueryType.SIMPLE)
        (False, "Contains preamble: ^based on (the |your )?data")
        
        >>> _validate_response_format("Technology leads. Furniture lags. Office supplies are stable. Consumer is growing.", QueryType.SIMPLE)
        (False, "Too many sentences: 4 > 1")
    """
    # 1. Check sentence count
    # Split on sentence terminators (. ! ?) followed by space and capital letter
    # This regex finds sentence boundaries
    sentences = re.split(r'[.!?]\s+(?=[A-Z])', response)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    max_sentences = 1 if query_type == QueryType.SIMPLE else 3
    if len(sentences) > max_sentences:
        return False, f"Too many sentences: {len(sentences)} > {max_sentences}"
    
    # 2. Check for preambles - response should not start with these patterns
    preamble_patterns = [
        r'^based on (the |your )?data',
        r'^looking at',
        r'^let me (analyze|look|check)',
        r'^i can see',
        r'^the data shows',
        r'^analyzing (the |your )?data',
        r'^from (the |your )?data'
    ]
    
    response_lower = response.lower()
    for pattern in preamble_patterns:
        if re.match(pattern, response_lower):
            return False, f"Contains preamble: {pattern}"
    
    # 3. Check for dataset reference
    # Should contain at least one of: number, possessive, or column reference
    has_number = bool(re.search(r'\d+', response))
    has_possessive = any(word in response_lower for word in ['your', 'this dataset', 'the data'])
    
    # Note: We can't check for actual column names without dataset context
    # So we accept the response if it has numbers OR possessive references
    if not (has_number or has_possessive):
        return False, "No dataset reference found"
    
    # 4. Check for technical jargon (all query types, but especially important for COMPLEX)
    jargon_terms = [
        'statistical significance', 'p-value', 'correlation coefficient',
        'standard deviation', 'hypothesis', 'null hypothesis'
    ]
    
    for term in jargon_terms:
        if term in response_lower:
            return False, f"Contains jargon: {term}"
    
    # 5. Check for academic transitions
    academic_patterns = [
        r'\btherefore\b', r'\bthus\b', r'\bin conclusion\b',
        r'\bfurthermore\b', r'\bmoreover\b', r'\bhence\b'
    ]
    
    for pattern in academic_patterns:
        if re.search(pattern, response_lower):
            return False, f"Contains academic transition: {pattern}"
    
    # All checks passed
    return True, ""


def _build_enhanced_prompt(
    df: pd.DataFrame,
    question: str,
    history: Optional[list] = None,
    query_type: QueryType = QueryType.SIMPLE,
    dataset_ctx: Optional[dict] = None
) -> str:
    """
    Build optimized prompt with response guidelines and examples.
    
    Constructs a comprehensive prompt for the LLM that includes:
    - System instructions with role, length constraints, and tone guidelines
    - Response length constraints based on query type (1 sentence for SIMPLE, 3 for COMPLEX)
    - Example responses demonstrating desired format
    - Conversation history (last 4 exchanges, truncated to 500 chars each)
    - Compact dataset context summary (record count, columns, top 3 numeric stats)
    - Current user question
    
    The prompt is optimized to stay under 800 tokens total to ensure fast response times
    while providing sufficient context for accurate, contextual answers.
    
    Args:
        df: Dataset being analyzed
        question: User's current question (empty string for general insights)
        history: Conversation history (list of message dicts with 'role' and 'content')
        query_type: Query complexity classification (SIMPLE or COMPLEX)
        dataset_ctx: Pre-formatted dataset context from _format_dataset_context()
    
    Returns:
        Complete prompt string ready for LLM input
    
    Examples:
        >>> df = pd.DataFrame({'Sales': [100, 200], 'Category': ['A', 'B']})
        >>> ctx = _format_dataset_context(df)
        >>> prompt = _build_enhanced_prompt(df, "Which sells more?", None, QueryType.SIMPLE, ctx)
        >>> "one sentence" in prompt
        True
        >>> "conversational business language" in prompt
        True
    """
    # System instructions based on query type
    length_constraint = "one sentence" if query_type == QueryType.SIMPLE else "up to three sentences"
    
    system_parts = [
        "You are an expert business analyst providing insights to a client.",
        f"Answer in {length_constraint}.",
        "Use conversational business language - be direct and casual.",
        "Always reference the client's specific dataset (mention record count).",
        "Start your answer immediately - no preambles like 'Based on the data' or 'Looking at'.",
        "Use casual comparatives ('sells more', 'doing better') not formal terms.",
        "Avoid technical jargon (correlation, significance, deviation).",
        "Avoid academic phrases (Therefore, Thus, In conclusion).",
    ]
    
    # Add query-type specific guidelines
    if query_type == QueryType.COMPLEX:
        system_parts.append("Include specific numbers with proper formatting (1,234 not 1234).")
        system_parts.append("Round percentages to 2 decimals, counts to whole numbers.")
    else:
        system_parts.append("Don't include numbers unless specifically asked.")
    
    # Examples based on query type
    examples = []
    if query_type == QueryType.SIMPLE:
        examples = [
            "Q: Which category sells more?",
            "A: Technology sells more in your 847 records.",
            "",
            "Q: Who is the top customer?",
            "A: Sean Miller leads with the highest order total across your 1,200 transactions."
        ]
    else:
        examples = [
            "Q: What are the sales trends?",
            "A: Your 2,340 orders show steady growth from Jan to Jun, with Technology driving 45% of revenue at $125,000. Consumer products lag at $78,000 but improved 15% in Q2.",
            "",
            "Q: Compare performance across regions.",
            "A: In your dataset, West region dominates with 1,250 orders ($310,000), while East has only 890 orders ($210,000). Central region shows strongest growth rate at 22% quarter-over-quarter."
        ]
    
    # Build prompt parts
    prompt_parts = [
        "\n".join(system_parts),
        "",
        "Examples:",
        "\n".join(examples),
        ""
    ]
    
    # Add conversation history (last 4 exchanges, truncate to 500 chars)
    if history:
        prompt_parts.append("Previous conversation:")
        for msg in history[-4:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content:
                # Truncate to 500 chars
                if len(content) > 500:
                    content = content[:500] + "..."
                prompt_parts.append(f"{role.title()}: {content}")
        prompt_parts.append("")
    
    # Dataset context (compact summary)
    if dataset_ctx:
        ctx_summary = (
            f"Dataset: {dataset_ctx['record_count_formatted']} records, "
            f"{dataset_ctx['num_columns']} columns ({', '.join(dataset_ctx['column_names'][:5])}"
        )
        if len(dataset_ctx['column_names']) > 5:
            ctx_summary += f", +{len(dataset_ctx['column_names']) - 5} more"
        ctx_summary += ")"
        
        # Add brief stats for numeric columns (top 3 only)
        if dataset_ctx['numeric_columns']:
            nums = df.select_dtypes(include=np.number)
            for col in dataset_ctx['numeric_columns'][:3]:
                if col in nums.columns:
                    ctx_summary += f"\n{col}: mean={nums[col].mean():.1f}, range=[{nums[col].min():.1f}, {nums[col].max():.1f}]"
        
        prompt_parts.append(ctx_summary)
        prompt_parts.append("")
    
    # Current question
    if question:
        prompt_parts.append(f"Client: {question}")
        prompt_parts.append("You:")
    else:
        prompt_parts.append("Provide 3-5 key insights in natural language (complete sentences, reference specific numbers).")
        prompt_parts.append("Your insights:")
    
    return "\n".join(prompt_parts)


# -- Gemini client -------------------------------------------------------------

def _get_gemini_client():
    """Get Gemini provider instance"""
    from app.ai import gemini_flash
    return gemini_flash


# -- Data summary (token-efficient) --------------------------------------------

def _compact_summary(df: pd.DataFrame, max_rows: int = 5) -> str:
    nums = df.select_dtypes(include=np.number)
    cats = df.select_dtypes(include="object")
    lines = [
        f"Shape: {df.shape[0]} rows  {df.shape[1]} columns",
        f"Columns: {list(df.columns)}",
        f"Numeric: {nums.columns.tolist()}",
        f"Categorical: {cats.columns.tolist()}",
        f"Missing: {df.isnull().sum()[df.isnull().sum()>0].to_dict()}",
    ]
    if not nums.empty:
        desc = nums.describe().loc[["mean","std","min","max"]].round(2)
        lines.append(f"Stats:\n{desc.to_string()}")
    if not cats.empty:
        for col in cats.columns[:3]:
            lines.append(f"{col} samples: {df[col].value_counts().head(5).to_dict()}")
    lines.append(f"\nFirst {max_rows} rows:\n{df.head(max_rows).to_string()}")
    return "\n".join(lines)


# -- Safe code execution -------------------------------------------------------

_SAFE_BUILTINS = {
    "len": len, "range": range, "list": list, "dict": dict,
    "str": str, "int": int, "float": float, "bool": bool,
    "round": round, "abs": abs, "sum": sum, "min": min, "max": max,
    "sorted": sorted, "enumerate": enumerate, "zip": zip,
    "print": print, "type": type, "isinstance": isinstance,
}

def _execute_code(code: str, df: pd.DataFrame):
    """Execute LLM-generated pandas code safely."""
    # Strip markdown fences
    code = re.sub(r"```(?:python)?|```", "", code).strip()

    local = {
        "df": df.copy(),
        "pd": pd,
        "np": np,
        "__builtins__": _SAFE_BUILTINS,
    }
    exec(code, local)
    return local.get("result")


# -- Main query function -------------------------------------------------------

def run_llm_query(question: str, df: Optional[pd.DataFrame],
                  user_id: str = "", history: list = None):
    """
    Generate and execute pandas code via Gemini LLM.
    Uses conversation history for context-aware responses.
    """
    from app.core.config import GEMINI_API_KEY
    
    if not GEMINI_API_KEY:
        return None, "", "No Gemini API key configured"

    try:
        gemini = _get_gemini_client()
        summary = _compact_summary(df) if df is not None else "No dataset loaded."

        system_content = f"""You are an expert Python data analyst with access to a pandas DataFrame named 'df'.

Dataset summary:
{summary}

Rules:
- Write ONLY executable Python pandas/numpy code
- Store the final answer in a variable named 'result'
- result should be a DataFrame, Series, scalar, or list
- No explanations, no markdown fences, no print statements
- Use df.copy() if modifying the dataframe"""

        # Build prompt with history
        prompt_parts = [system_content]
        
        if history:
            for msg in history[-6:]:  # last 3 exchanges
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"\n{role.title()}: {content}")
        
        prompt_parts.append(f"\nUser: {question}\n\nAssistant: Here's the Python code:")
        full_prompt = "\n".join(prompt_parts)

        # Get response from Gemini (sync wrapper for async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        code = loop.run_until_complete(
            gemini.generate_text(full_prompt, max_tokens=600, temperature=0.1)
        )
        loop.close()
        
        code = code.strip()

        if df is not None:
            result = _execute_code(code, df)
        else:
            result = None

        return result, code, "success"

    except Exception as e:
        return None, "", str(e)


# -- Insight generation --------------------------------------------------------

def run_insight(df: Optional[pd.DataFrame], api_key: str,
                history: list = None, question: str = "") -> str:
    """
    Generate natural language insights from dataset.
    
    Enhanced to provide concise, contextual responses:
    - Simple queries: 1 sentence max
    - Complex queries: 3 sentences max
    - Response time target: < 2 seconds
    
    Args:
        df: Dataset to analyze
        api_key: Gemini API key (legacy, not used)
        history: Conversation history (list of message dicts)
        question: User's question (empty for general insights)
    
    Returns:
        Natural language response string
    """
    start_time = time.time()
    
    if df is None:
        return "No dataset loaded. Upload a file first."
    
    try:
        # 1. Classify query (default to COMPLEX for general insights)
        query_type = _classify_query(question) if question else QueryType.COMPLEX
        
        # 2. Format dataset context
        dataset_ctx = _format_dataset_context(df)
        
        # 3. Build enhanced prompt
        prompt = _build_enhanced_prompt(
            df=df,
            question=question,
            history=history,
            query_type=query_type,
            dataset_ctx=dataset_ctx
        )
        
        # 4. Generate response with optimized settings
        gemini = _get_gemini_client()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Token limits: Simple=512, Complex=1024, General=1024
        if query_type == QueryType.SIMPLE:
            max_tokens = 512
        elif question:
            max_tokens = 1024
        else:
            max_tokens = 1024
        
        response = loop.run_until_complete(
            gemini.generate_text(
                prompt, 
                max_tokens=max_tokens,
                temperature=0.2  # Lower for more consistent formatting
            )
        )
        loop.close()
        
        response = response.strip()
        
        # 5. Validate response format
        is_valid, error_msg = _validate_response_format(response, query_type)
        if not is_valid:
            logger.debug(f"Response validation warning: {error_msg}")
        
        # 6. Monitor performance
        duration = time.time() - start_time
        if duration > 2.0:
            logger.warning(
                f"Slow insight generation: {duration:.2f}s for query: {question[:100]}"
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating insight: {e}")
        return f"Could not generate insights: {e}"


# -- Smart chart type selection ------------------------------------------------

def select_chart_type(result_df: pd.DataFrame, question: str) -> str:
    """Ask Gemini to pick the best chart type for the result."""
    try:
        gemini = _get_gemini_client()
        cols = list(result_df.columns) if hasattr(result_df, "columns") else []
        dtypes = {c: str(t) for c, t in result_df.dtypes.items()} if hasattr(result_df, "dtypes") else {}

        prompt = (
            f"Question: {question}\nResult columns: {cols}\nDtypes: {dtypes}\n\n"
            "Return ONLY one word: bar, line, scatter, pie, histogram, heatmap, or table"
        )
        
        # Get response from Gemini (sync wrapper)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            gemini.generate_text(prompt, max_tokens=10, temperature=0)
        )
        loop.close()
        
        return response.strip().lower()
    except Exception:
        return "table"
