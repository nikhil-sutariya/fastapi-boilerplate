from typing import Optional, List, Dict, Any, Union
from bson import ObjectId
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult
from app.core.logging import setup_logger
from app.core.custom_model_fields import mongo_to_dict, dict_to_mongo

logger = setup_logger()

async def store_bulk_document(collection: AsyncIOMotorCollection, document_data: List[Dict[str, Any]]) -> Optional[InsertManyResult]:
    try:
        result = await collection.insert_many(document_data)
        return result
    except Exception as e:
        logger.error("Error while storing bulk documents: ", str(e))
        return None

async def store_document(collection: AsyncIOMotorCollection, document_data: Dict[str, Any]) -> Optional[str]:
    try:
        document_data['created_at'] = datetime.now(timezone.utc)
        document_data['updated_at'] = datetime.now(timezone.utc)
        
        # Convert id to _id for MongoDB storage
        mongo_data = dict_to_mongo(document_data.copy())
        
        result = await collection.insert_one(mongo_data)
        return str(result.inserted_id)
    except Exception as e:  
        logger.error("Error while storing document: %s", str(e))
        return None
    
async def edit_document(collection: AsyncIOMotorCollection, document_id: str, document_data: Dict[str, Any]) -> Optional[str]:
    try:
        document_data['updated_at'] = datetime.now(timezone.utc)
        await collection.update_one(
            {"_id": ObjectId(document_id)}, 
            {"$set": document_data}
        )
        return str(document_id)
    except Exception as e:
        logger.error("Error while editing document: ", str(e))
        return None

async def get_document_data(collection: AsyncIOMotorCollection, document_id: Optional[str] = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
    try:
        if document_id:
            document_data = await collection.find_one({"_id": ObjectId(document_id)})
            if not document_data:
                return None
            # Convert _id to id for API usage
            return mongo_to_dict(document_data)
        else:
            all_document_data = await collection.find().to_list(length=None)
            # Convert all documents _id to id for API usage
            return [mongo_to_dict(doc) for doc in all_document_data]
        
    except Exception as e:
        logger.error("Error while getting document data: ", str(e))
        return None
    
async def filter_document_data(collection: AsyncIOMotorCollection, filter: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    try:
        document_data = await collection.find(filter).to_list(length=None)
        # Convert all documents _id to id for API usage
        return [mongo_to_dict(doc) for doc in document_data]
    except Exception as e:
        logger.error("Error while getting document data: ", str(e))
        return None

async def delete_document(collection: AsyncIOMotorCollection, document_id: str) -> Optional[DeleteResult]:
    try:
        result = await collection.delete_one({"_id": ObjectId(document_id)})
        return result
    except Exception as e:
        logger.error("Error while deleting document: ", str(e))
        return None
    