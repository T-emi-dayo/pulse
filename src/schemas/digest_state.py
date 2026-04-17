from pydantic import BaseModel

class Digest(BaseModel):
    title: str
    content: str