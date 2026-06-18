import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config.settings import settings
from backend.database.session import engine, Base

# Import routers
from backend.routes.auth import router as auth_router
from backend.routes.documents import router as documents_router
from backend.routes.chat import router as chat_router
from backend.routes.admin import router as admin_router

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize database tables
try:
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize database tables: {str(e)}")

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready AI Research Assistant Backend powered by LangChain and LangGraph",
    version="1.0.0"
)

# CORS Configuration
# In production, specify actual allowed origins instead of wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for general internal server errors
@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception occurred on request {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the administrator."}
    )

# Include API routes
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(admin_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "supported_features": [
            "User Authentication (JWT)",
            "Multi-format Document Upload (PDF, DOCX, TXT)",
            "ChromaDB Ingestion",
            "LangGraph workflow execution (Query Analysis -> Retrieval -> Context Evaluation -> Generation -> Verification)",
            "Citations and Chat History Logs",
            "Admin Statistics and Usage Analytics"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    # Start the app locally on port 8000
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
