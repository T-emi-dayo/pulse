class Deduplication(BaseModel):
    """Model to represent the deduplication state of an agent"""
    dropped_sources: List[str]