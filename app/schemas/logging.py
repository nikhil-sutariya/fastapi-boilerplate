from pydantic import BaseModel

class AppLogSchema(BaseModel):
    _id: str
    entity_id: str | None = None
    user_id: str
    message: str
    module: str
    log_type: str

class LogSchema(BaseModel):
    _id: str
    entity_id: str | None = None
    user_id: str
    message: str
    module: str
    log_type: str
