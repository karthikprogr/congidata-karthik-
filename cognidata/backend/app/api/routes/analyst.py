"""
Option A - AI Data Analyst (Most Powerful)
Multi-turn reasoning, auto-suggest next questions, confidence scores,
autonomous insight generation, decision recommendations.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user, get_api_key

router = APIRouter(prefix="/analyst", tags=["Analyst"])


class ReasonRequest(BaseModel):
    question: str
    depth: int = 3          # reasoning steps
    auto_suggest: bool = True


class AutoInsightRequest(BaseModel):
    focus: str = "general"  # general | anomaly | trend | comparison | decision
    max_insights: int = 5


class DecisionRequest(BaseModel):
    goal: str               # e.g. "increase revenue", "reduce churn"
    constraints: str = ""   # e.g. "budget < $10k"


# - Deep reasoning chain -

@router.post("/reason")
async def deep_reason(req: ReasonRequest,
                      api_key: str = Depends(get_api_key),
                      user: dict = Depends(get_current_user)):
    """
    Multi-step reasoning chain. Breaks question into sub-questions,
    answers each, synthesizes final answer with confidence score.
    """
    from app.services.data_store import get as get_df
    import numpy as np
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(400, "No dataset loaded. Upload data first.")

    # Build dataset context
    nums = df.select_dtypes(include=np.number)
    context = f"Dataset: {df.shape[0]} rows - {df.shape[1]} cols\n"
    context += f"Columns: {list(df.columns)}\n"
    if not nums.empty:
        context += f"Numeric stats:\n{nums.describe().round(2).to_string()}\n"
    # Sample rows
    context += f"\nSample (5 rows):\n{df.head(5).to_string()}\n"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Step 1: Decompose question
        decompose_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analyst. Break the user's question into 2-3 specific sub-questions that together answer the main question. Return as JSON array of strings."},
                {"role": "user", "content": f"Question: {req.question}\n\nDataset context:\n{context[:1000]}"}
            ],
            max_tokens=300, temperature=0.1,
            response_format={"type": "json_object"},
        )
        import json
        try:
            sub_qs = json.loads(decompose_resp.choices[0].message.content).get("questions", [req.question])
        except Exception:
            sub_qs = [req.question]

        # Step 2: Answer each sub-question
        chain = []
        for sq in sub_qs[:req.depth]:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a data analyst. Answer concisely using the dataset.\n\n{context[:2000]}"},
                    {"role": "user", "content": sq}
                ],
                max_tokens=400, temperature=0.1,
            )
            chain.append({"question": sq, "answer": resp.choices[0].message.content})

        # Step 3: Synthesize + confidence
        synthesis_prompt = f"""Based on these analysis steps, provide:
1. A final comprehensive answer to: "{req.question}"
2. A confidence score (0-100) based on data quality and completeness
3. Key caveats or limitations

Analysis chain:
{json.dumps(chain, indent=2)}

Return as JSON: {{"answer": "...", "confidence": 85, "caveats": ["..."]}}"""

        synth_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior data analyst. Synthesize findings into a clear decision-ready answer."},
                {"role": "user", "content": synthesis_prompt}
            ],
            max_tokens=600, temperature=0.1,
            response_format={"type": "json_object"},
        )
        try:
            synthesis = json.loads(synth_resp.choices[0].message.content)
        except Exception:
            synthesis = {"answer": synth_resp.choices[0].message.content, "confidence": 70, "caveats": []}

        # Step 4: Auto-suggest follow-up questions
        suggestions = []
        if req.auto_suggest:
            suggest_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Suggest 3 follow-up questions a data analyst would ask next. Return JSON array."},
                    {"role": "user", "content": f"Original question: {req.question}\nAnswer: {synthesis.get('answer','')[:300]}\nDataset columns: {list(df.columns)}"}
                ],
                max_tokens=200, temperature=0.3,
                response_format={"type": "json_object"},
            )
            try:
                suggestions = json.loads(suggest_resp.choices[0].message.content).get("questions", [])
            except Exception:
                suggestions = []

        return {
            "question": req.question,
            "reasoning_chain": chain,
            "answer": synthesis.get("answer", ""),
            "confidence": synthesis.get("confidence", 70),
            "caveats": synthesis.get("caveats", []),
            "suggested_questions": suggestions,
            "steps": len(chain),
        }

    except Exception as e:
        raise HTTPException(500, f"Reasoning failed: {e}")


# - Autonomous insight generation -

@router.post("/auto-insights")
async def auto_insights(req: AutoInsightRequest,
                        api_key: str = Depends(get_api_key),
                        user: dict = Depends(get_current_user)):
    """
    Autonomously scan the dataset and generate the most important insights
    without the user asking anything.
    """
    from app.services.data_store import get as get_df
    import numpy as np, pandas as pd
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(400, "No dataset loaded.")

    # Pre-compute stats for the LLM
    nums = df.select_dtypes(include=np.number)
    cats = df.select_dtypes(include="object")

    stats_summary = ""
    if not nums.empty:
        desc = nums.describe().round(2)
        stats_summary += f"Numeric stats:\n{desc.to_string()}\n\n"
        # Correlations
        if len(nums.columns) > 1:
            corr = nums.corr().round(2)
            high_corr = []
            for i in range(len(corr.columns)):
                for j in range(i+1, len(corr.columns)):
                    v = corr.iloc[i, j]
                    if abs(v) > 0.6:
                        high_corr.append(f"{corr.columns[i]} - {corr.columns[j]}: {v}")
            if high_corr:
                stats_summary += f"High correlations: {', '.join(high_corr[:5])}\n"

    if not cats.empty:
        for col in cats.columns[:3]:
            vc = df[col].value_counts().head(5)
            stats_summary += f"\n{col} top values: {vc.to_dict()}\n"

    # Null summary
    nulls = df.isnull().sum()
    null_cols = nulls[nulls > 0]
    if not null_cols.empty:
        stats_summary += f"\nMissing values: {null_cols.to_dict()}\n"

    try:
        from openai import OpenAI
        import json
        client = OpenAI(api_key=api_key)

        focus_prompts = {
            "general": "Generate the most important business insights from this dataset.",
            "anomaly": "Focus on outliers, anomalies, and unusual patterns.",
            "trend": "Focus on trends, growth patterns, and time-based changes.",
            "comparison": "Focus on comparisons between groups, segments, or categories.",
            "decision": "Focus on actionable recommendations and decisions the business should make.",
        }
        focus_prompt = focus_prompts.get(req.focus, focus_prompts["general"])

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are an autonomous data analyst. {focus_prompt}
Return exactly {req.max_insights} insights as JSON array, each with:
- title (short, punchy)
- insight (2-3 sentences)
- importance (high/medium/low)
- action (what to do about it)
- confidence (0-100)

Return: {{"insights": [...]}}"""},
                {"role": "user", "content": f"Dataset: {df.shape[0]} rows - {df.shape[1]} cols\nColumns: {list(df.columns)}\n\n{stats_summary[:3000]}"}
            ],
            max_tokens=1500, temperature=0.2,
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.choices[0].message.content)
        insights = result.get("insights", [])
        return {
            "focus": req.focus,
            "dataset_shape": list(df.shape),
            "insights": insights,
            "count": len(insights),
        }
    except Exception as e:
        raise HTTPException(500, f"Auto-insights failed: {e}")


# - Decision engine -

@router.post("/decide")
async def decision_engine(req: DecisionRequest,
                          api_key: str = Depends(get_api_key),
                          user: dict = Depends(get_current_user)):
    """
    Given a business goal, analyze the data and return ranked action recommendations.
    """
    from app.services.data_store import get as get_df
    import numpy as np
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(400, "No dataset loaded.")

    nums = df.select_dtypes(include=np.number)
    context = f"Dataset: {df.shape[0]} rows - {df.shape[1]} cols\nColumns: {list(df.columns)}\n"
    if not nums.empty:
        context += f"Stats:\n{nums.describe().round(2).to_string()}\n"

    try:
        from openai import OpenAI
        import json
        client = OpenAI(api_key=api_key)

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are a strategic data analyst and decision advisor.
Given a business goal and dataset, return ranked action recommendations as JSON:
{"goal": "...", "recommendations": [{"rank": 1, "action": "...", "rationale": "...", "expected_impact": "...", "effort": "low|medium|high", "confidence": 85}], "risks": ["..."], "kpis_to_track": ["..."]}"""},
                {"role": "user", "content": f"Goal: {req.goal}\nConstraints: {req.constraints}\n\nData context:\n{context[:2500]}"}
            ],
            max_tokens=1000, temperature=0.2,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        raise HTTPException(500, f"Decision engine failed: {e}")


# - Narrative report -

@router.post("/narrate")
async def narrate_data(api_key: str = Depends(get_api_key),
                       user: dict = Depends(get_current_user)):
    """
    Option B - Autonomous report narration.
    Generate a full executive narrative from the dataset without any prompting.
    """
    from app.services.data_store import get as get_df
    import numpy as np
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(400, "No dataset loaded.")

    nums = df.select_dtypes(include=np.number)
    context = f"Dataset: {df.shape[0]} rows - {df.shape[1]} cols\nColumns: {list(df.columns)}\n"
    if not nums.empty:
        context += f"Stats:\n{nums.describe().round(2).to_string()}\n"
        context += f"\nSample:\n{df.head(10).to_string()}\n"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior business analyst writing an executive data narrative. Write in clear, professional prose. Include: executive summary, key findings (3-5), trends, risks, and recommended next steps."},
                {"role": "user", "content": f"Write a complete data narrative for this dataset:\n\n{context[:3000]}"}
            ],
            max_tokens=1200, temperature=0.3,
        )
        narrative = resp.choices[0].message.content
        return {
            "narrative": narrative,
            "dataset_shape": list(df.shape),
            "word_count": len(narrative.split()),
        }
    except Exception as e:
        raise HTTPException(500, f"Narration failed: {e}")
