from pydantic import BaseModel, Field
from typing import List

class Sources(BaseModel):
    id: int = Field(..., ge=1, description="Module numeric identifier (>= 1).")
    title: str
    url: str
    summary: str | None = None
    channel: str | None = None
    
class SourceTypes(BaseModel):
    type_name: str
    Sources : List[Sources]

class IngestionState(BaseModel):
    source_types : List[SourceTypes]
    sources_found : int