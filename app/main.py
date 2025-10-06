from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import setup_logger
from app.core.response import CustomException
from app.db.database import lifespan
from app.api.routes.logging import log_router
from app.api.routes.auth import auth_router
from typing import Dict

settings = get_settings()
logger = setup_logger()

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.client_origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
    return JSONResponse(
            status_code=exc.status,
            content=jsonable_encoder({
                "status_code": exc.status, 
                "message": exc.message,
                "error": exc.errors
            })
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = exc.errors()
    logger.error(str(details[0]['loc']))

    if details[0]['type'] == 'string_too_short':
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({
                "status_code": 422, 
                "message": "Please provide valid value",
                "error_message": details[0]['msg']
            })
        )

    if 'email' in details[0]['loc']:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({
                "status_code": 422, 
                "message": details[0]['msg'].split(",")[-1].lstrip(),
                "error_message": details[0]['msg']
            })
        )
    
    if 'password' in details[0]['loc']:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({
                "status_code": 422, 
                "message": details[0]['msg'].split(",")[-1].lstrip(),
                "error_message": details[0]['msg']
            })
        )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
                "status_code": 422, 
                "message": details[0]['msg'].split(",")[-1].lstrip(),
                "error_message": details[0]['msg'],
                "detail": exc.errors(),
            }
        )
    )

app.include_router(auth_router, tags=['Auth'], prefix='/api/v1/auth')
app.include_router(log_router, tags=['Logs'], prefix='/api/v1/logs')

@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Welcome to FatAPI"}
