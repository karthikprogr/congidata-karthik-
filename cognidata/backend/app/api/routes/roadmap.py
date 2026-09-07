"""Roadmap routes - CRUD + AI generation."""
import sys, pathlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_current_user, get_api_key

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])

# In-memory store (replace with DB for production)
_features: list[dict] = []
_next_id = 1

class FeatureCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "Medium"
    category: str = "Feature"
    status: str = "Planned"
    tags: str = ""  # comma-separated


class FeatureUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[str] = None

class GenerateRequest(BaseModel):
    prompt: str
    count: int = 5

@router.get("/features")
def list_features(user: dict = Depends(get_current_user)):
    return [f for f in _features if f.get("owner") == user["email"]]

@router.post("/features", status_code=201)
def create_feature(data: FeatureCreate, user: dict = Depends(get_current_user)):
    global _next_id
    feature = {**data.model_dump(), "id": _next_id, "owner": user["email"]}
    _features.append(feature)
    _next_id += 1
    return feature

@router.patch("/features/{feature_id}")
def update_feature(feature_id: int, data: FeatureUpdate, user: dict = Depends(get_current_user)):
    for f in _features:
        if f["id"] == feature_id and f["owner"] == user["email"]:
            if data.status is not None: f["status"] = data.status
            if data.priority is not None: f["priority"] = data.priority
            if data.tags is not None: f["tags"] = data.tags
            return f
    raise HTTPException(404, "Feature not found")

@router.delete("/features/{feature_id}", status_code=204)
def delete_feature(feature_id: int, user: dict = Depends(get_current_user)):
    global _features
    _features = [f for f in _features if not (f["id"] == feature_id and f["owner"] == user["email"])]

@router.post("/generate")
def generate_features(req: GenerateRequest, api_key: str = Depends(get_api_key),
                      user: dict = Depends(get_current_user)):
    global _next_id
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content":
                f"Generate {req.count} product roadmap features for: {req.prompt}\n\n"
                "Return as JSON array with fields: title, description, priority (High/Medium/Low), category (Feature/Enhancement/Infrastructure)\n"
                "Return ONLY the JSON array, no explanation."}],
            temperature=0.7, max_tokens=1000,
        )
        import json, re
        content = resp.choices[0].message.content.strip()
        content = re.sub(r"```(?:json)?|```", "", content).strip()
        items = json.loads(content)
        created = []
        for item in items[:req.count]:
            feature = {
                "id": _next_id, "owner": user["email"],
                "title": item.get("title","Feature"),
                "description": item.get("description",""),
                "priority": item.get("priority","Medium"),
                "category": item.get("category","Feature"),
                "status": "Planned",
            }
            _features.append(feature)
            created.append(feature)
            _next_id += 1
        return {"created": len(created), "features": created}
    except Exception as e:
        raise HTTPException(422, str(e))
