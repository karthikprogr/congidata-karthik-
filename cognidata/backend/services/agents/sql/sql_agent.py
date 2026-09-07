"""
SQL Agent — NL→pandas code with schema context → validate → execute → auto-fix on error.
Now powered by Gemini for better code generation.
"""
import os
import re
import pandas as pd
import asyncio
from typing import Optional
from services.agents.sql.schema import dataframe_schema


def run_sql_agent(question: str, df: Optional[pd.DataFrame],
                  api_key: str, history: list = None) -> dict:
    """Convert natural language to pandas code and execute it using Gemini."""
    if df is None:
        return {"error": "No dataset loaded", "code": "", "result": None}

    schema = dataframe_schema(df)
    context = ""
    if history:
        context = "\n".join(f"{h['role']}: {h['content']}" for h in history[-4:])

    prompt = f"""You are a Python data analyst. A pandas DataFrame named 'df' is available.

Schema:
{schema}

{f'Recent conversation:{chr(10)}{context}' if context else ''}

Question: {question}

Write ONLY executable Python pandas code.
- Store the final result in a variable named 'result'
- result should be a DataFrame, Series, scalar, or list
- No explanations, no markdown fences, no print statements
- Use df.copy() if modifying data"""

    try:
        from app.ai import gemini_flash
        
        # Generate code with Gemini
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            gemini_flash.generate_text(prompt, max_tokens=500, temperature=0.1)
        )
        code = response.strip()
        loop.close()
        
        code = re.sub(r"```(?:python)?|```", "", code).strip()

        result, error = _execute(code, df)

        # Auto-fix on error using Gemini
        if error and result is None:
            fix_prompt = f"This pandas code has an error:\n{code}\nError: {error}\nFix it. Return only the corrected code."
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            fix_response = loop.run_until_complete(
                gemini_flash.generate_text(fix_prompt, max_tokens=400, temperature=0.1)
            )
            fixed_code = re.sub(r"```(?:python)?|```", "", fix_response.strip()).strip()
            loop.close()
            
            result, error = _execute(fixed_code, df)
            if result is not None:
                code = fixed_code + "\n# (auto-fixed by Gemini)"

        return {"result": result, "code": code, "error": error}

    except Exception as e:
        return {"error": str(e), "code": "", "result": None}


def _execute(code: str, df: pd.DataFrame):
    """Execute pandas code safely."""
    import numpy as np
    local = {"df": df.copy(), "pd": pd, "np": np,
             "__builtins__": {"len": len, "range": range, "list": list,
                              "str": str, "int": int, "float": float,
                              "round": round, "abs": abs, "sum": sum,
                              "min": min, "max": max, "sorted": sorted,
                              "print": print, "type": type}}
    try:
        exec(code, local)
        return local.get("result"), None
    except Exception as e:
        return None, str(e)
