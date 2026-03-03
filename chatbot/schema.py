from pydantic import BaseModel


class UserQuery(BaseModel):
    user_id: str
    message: str

class UserResponse(BaseModel):
    response: str
    intent: str
    confidence: float