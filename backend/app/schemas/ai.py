from pydantic import BaseModel

class AIMessage(BaseModel):
    role: str
    content: str
    
class AIMessages(BaseModel):
    messages: list[AIMessage]