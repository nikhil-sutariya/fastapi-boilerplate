from pydantic import GetCoreSchemaHandler, BaseModel, Field
from bson import ObjectId
from pydantic_core import core_schema
from typing import Any, Dict, Optional, Type, TypeVar
from datetime import datetime

T = TypeVar('T', bound='BaseModel')

class PyObjectId(ObjectId):
    """
    Custom ObjectId class for Pydantic v2 that handles MongoDB _id field seamlessly.
    This allows storing as _id in MongoDB but using 'id' in the API.
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(cls.validate),
            json_schema=core_schema.with_info_plain_validator_function(cls.validate),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def validate(cls, value: Any, _info: Any) -> ObjectId:
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)
        raise ValueError("Invalid ObjectId")

class MongoModel(BaseModel):
    """
    Base model for MongoDB documents that handles _id to id mapping seamlessly.
    This is the production-ready solution for MongoDB + FastAPI integration.
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id", description="Document ID")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        # Allow population by both field name and alias
        allow_population_by_field_name = True

    @classmethod
    def from_mongo(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create model instance from MongoDB document.
        Handles the _id to id conversion automatically.
        """
        if data is None:
            return None
        
        # Convert _id to id for Pydantic model
        if "_id" in data:
            data["id"] = str(data["_id"])
            # Remove _id to avoid conflicts
            data.pop("_id", None)
        
        return cls(**data)

    def to_mongo(self) -> Dict[str, Any]:
        """
        Convert model instance to MongoDB document format.
        Handles the id to _id conversion automatically.
        """
        data = self.model_dump(by_alias=True, exclude_none=True)
        
        # Convert id to _id for MongoDB
        if "id" in data and data["id"] is not None:
            data["_id"] = ObjectId(data["id"])
            # Remove id to avoid conflicts
            data.pop("id", None)
        
        return data

    def to_api_response(self) -> Dict[str, Any]:
        """
        Convert model instance to API response format.
        Uses 'id' field (not _id) for API responses.
        """
        data = self.model_dump(by_alias=False, exclude_none=True)
        
        # Ensure id is a string for API responses
        if "id" in data and data["id"] is not None:
            data["id"] = str(data["id"])
        
        return data

def mongo_to_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Utility function to convert MongoDB document to dictionary with id field.
    This is used in repository functions for seamless conversion.
    """
    if data is None:
        return None
    
    # Convert _id to id
    if "_id" in data:
        data["id"] = str(data["_id"])
        data.pop("_id", None)
    
    return data

def dict_to_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Utility function to convert dictionary with id field to MongoDB document.
    This is used in repository functions for seamless conversion.
    """
    if data is None:
        return None
    
    # Convert id to _id
    if "id" in data and data["id"] is not None:
        data["_id"] = ObjectId(data["id"])
        data.pop("id", None)
    
    return data
