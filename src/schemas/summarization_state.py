from typing import List
from pydantic import BaseModel

class SourceSummary(BaseModel):
    source_type: str
    summary: str

class SummarizationState(BaseModel):
    """Model to represent the state of the summarization process"""
    source_summaries: List[SourceSummary]
    summary: str
    last_updated: str