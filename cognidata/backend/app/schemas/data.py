from pydantic import BaseModel
from typing import Any, Optional

class UploadResponse(BaseModel):
    message: str
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    memory_mb: float = 0.0

class PreviewResponse(BaseModel):
    data: list[dict[str, Any]]
    total_rows: int

class InfoResponse(BaseModel):
    rows: int
    columns: int
    column_names: list[str]
    columns_info: list[dict[str, Any]] = []
    numeric_columns: list[str] = []
    categorical_columns: list[str] = []
    dtypes: dict[str, str]
    missing_values: dict[str, int]
    memory_mb: float

class CleanResponse(BaseModel):
    message: str
    rows_before: int
    rows_after: int
    rows_removed: int = 0
    nulls_filled: int
