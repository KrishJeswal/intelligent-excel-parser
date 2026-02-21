from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any, Dict


Confidence = Literal["high", "medium", "low"]


class ColumnInput(BaseModel):
    column_index: int = Field(ge=0)
    original_header: str
    normalized_header: str
    unit_hint: Optional[str] = None
    asset_hint: Optional[str] = None


class ColumnMapping(BaseModel):
    column_index: int = Field(ge=0)
    param_name: Optional[str] = None  
    asset_name: Optional[str] = None  
    confidence: Confidence
    reason: str = Field(min_length=1)


class LLMMappingResponse(BaseModel):
    mappings: List[ColumnMapping]


class ParsedCell(BaseModel):
    row: int = Field(ge=1, description="1-indexed Excel row number")
    col: int = Field(ge=0, description="0-indexed column index")
    param_name: str
    asset_name: Optional[str] = None
    raw_value: Any = None
    parsed_value: Optional[float] = None
    confidence: Confidence


class UnmappedColumn(BaseModel):
    col: int = Field(ge=0)
    header: str
    reason: str


class ParseResponse(BaseModel):
    status: Literal["success", "error"]
    header_row: Optional[int] = Field(default=None, description="1-indexed Excel row number for detected header")
    parsed_data: List[ParsedCell] = Field(default_factory=list)
    unmapped_columns: List[UnmappedColumn] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

