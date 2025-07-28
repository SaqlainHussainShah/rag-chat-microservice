from pydantic import BaseModel

class MessageIn(BaseModel):
    sender: str
    content: str

class MessageCreateRequest(BaseModel):
    sender: str
    content: str

class MessageOut(BaseModel):
    id: str
    sender: str
    content: str
    timestamp: float

class Session(BaseModel):
    id: str
    name: str
    is_favorite: bool = False

class UploadTextRequest(BaseModel):
    file_path: str

class CreateSessionRequest(BaseModel):
    name: str

class RenameSessionRequest(BaseModel):
    new_name: str
    
class FavoriteSessionRequest(BaseModel):
    is_favorite: bool


class Message(BaseModel):
    id: str
    sender: str
    content: str
    timestamp: str

class RAGRequest(BaseModel):
    user_message: str