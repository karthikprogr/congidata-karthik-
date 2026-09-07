"""RAG routes - index dataset, query with context, list/manage datasets."""
import sys, pathlib
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from app.core.deps import get_current_user, get_api_key
from app.services.data_store import get as get_df, list_datasets, switch_dataset

router = APIRouter(prefix="/rag", tags=["RAG"])

def _boot():
    p = str(pathlib.Path(__file__).resolve().parents[3] / "services")
    if p not in sys.path: sys.path.insert(0, p)

class RAGQuery(BaseModel):
    question: str

class RAGDatasetInfo(BaseModel):
    name: str
    chunk_count: int
    indexed_at: str
    indexed: bool = True

class IndexResponse(BaseModel):
    message: str
    chunk_count: int
    dataset_name: str

@router.post("/index")
def index(user: dict = Depends(get_current_user)):
    _boot()
    from agents.rag.rag_agent import index_dataframe
    from app.services.data_store import _active
    df = get_df(user["email"])
    if df is None: raise HTTPException(404, "No dataset found")
    active_name = _active.get(user["email"], "dataset_1")
    count = index_dataframe(user["email"], df, active_name)
    return {"message": f"Indexed {count} chunks"}

@router.post("/query")
def query(req: RAGQuery, api_key: str = Depends(get_api_key),
          user: dict = Depends(get_current_user)):
    _boot()
    from agents.rag.rag_agent import query as rag_query
    answer = rag_query(user["email"], req.question, api_key)
    return {"answer": answer, "type": "text"}

@router.get("/status")
def status(user: dict = Depends(get_current_user)):
    _boot()
    from agents.rag.rag_agent import get_total_chunks
    count = get_total_chunks(user["email"])
    return {"chunks": count, "indexed": count > 0}

@router.get("/datasets", response_model=List[RAGDatasetInfo])
def list_rag_datasets(user: dict = Depends(get_current_user)):
    _boot()
    from agents.rag.rag_agent import list_indexed_datasets
    datasets = list_indexed_datasets(user["email"])
    return [
        RAGDatasetInfo(
            name=d["name"],
            chunk_count=d["chunk_count"],
            indexed_at=d["indexed_at"],
            indexed=True
        )
        for d in datasets
    ]

@router.post("/index/{dataset_name}", response_model=IndexResponse)
def index_specific_dataset(dataset_name: str, user: dict = Depends(get_current_user)):
    _boot()
    from agents.rag.rag_agent import index_dataframe
    user_datasets = list_datasets(user["email"])
    dataset_names = [d["name"] for d in user_datasets]
    if dataset_name not in dataset_names:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    switch_dataset(user["email"], dataset_name)
    df = get_df(user["email"])
    if df is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    chunk_count = index_dataframe(user["email"], df, dataset_name)
    return IndexResponse(message=f"Indexed {chunk_count} chunks", chunk_count=chunk_count, dataset_name=dataset_name)

@router.delete("/datasets/{dataset_name}")
def delete_rag_dataset(dataset_name: str, user: dict = Depends(get_current_user)):
    _boot()
    from agents.rag.rag_agent import delete_dataset
    success = delete_dataset(user["email"], dataset_name)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not indexed")
    return {"message": "Dataset removed from RAG index", "dataset_name": dataset_name}
