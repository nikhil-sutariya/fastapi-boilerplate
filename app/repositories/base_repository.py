from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from app.core.logging import setup_logger

logger = setup_logger()

async def store_bulk_document(collection, document_data: list):
    try:
        result = await collection.insert_many(document_data)
        return result
    except Exception as e:
        logger.error("Error while storing bulk documents: ", str(e))
        return None

async def store_document(collection, document_data: dict):
    try:
        document_data['created_at'] = datetime.now(timezone.utc)
        document_data['updated_at'] = datetime.now(timezone.utc)
        # Remove _id field as it shouldn't be updated
        document_data.pop("_id", None)
        result = await collection.insert_one(document_data)
        return str(result.inserted_id)
    except Exception as e:  
        logger.error("Error while storing document: %s", str(e))
        return None
    
async def edit_document(collection, document_id, document_data: dict):
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

async def get_document_data(collection, document_id: Optional[str] = None):
    try:
        if document_id:
            document_data = await collection.find_one({"_id": ObjectId(document_id)})
            if not document_data:
                return None
            return document_data
        else:
            all_document_data = await collection.find().to_list(length=None)
            return all_document_data
        
    except Exception as e:
        logger.error("Error while getting document data: ", str(e))
        return None
    
async def filter_document_data(collection, filter: dict):
    try:
        document_data = await collection.find(filter).to_list(length=None)
        return document_data
    except Exception as e:
        logger.error("Error while getting document data: ", str(e))
        return None

async def delete_document(collection, document_id):
    try:
        result = await collection.delete_one({"_id": ObjectId(document_id)})
        return result
    except Exception as e:
        logger.error("Error while deleting document: ", str(e))
        return None
    