import os
import shutil
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.models.db_models import User, Document, ChatMessage
from backend.models.schema_models import AdminStats
from backend.utils.deps import get_current_admin
from backend.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/stats", response_model=AdminStats)
def get_system_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get aggregated system statistics for dashboard analytics. Restricted to admin accounts.
    """
    # 1. Total counts
    total_users = db.query(User).count()
    total_documents = db.query(Document).count()
    total_queries = db.query(ChatMessage).filter(ChatMessage.role == "user").count()
    
    # 2. Get Chroma DB chunk count
    vector_service = VectorStoreService()
    chroma_chunks = vector_service.get_total_chunks_count()
    
    # 3. System disk storage statistics
    upload_dir = "./uploads"
    upload_size = 0
    if os.path.exists(upload_dir):
        for path, dirs, files in os.walk(upload_dir):
            for f in files:
                fp = os.path.join(path, f)
                upload_size += os.path.getsize(fp)
                
    total, used, free = shutil.disk_usage(".")
    
    # Convert sizes to MB
    upload_size_mb = round(upload_size / (1024 * 1024), 2)
    free_gb = round(free / (1024 * 1024 * 1024), 2)
    
    # 4. User details summary
    users = db.query(User).all()
    users_summary = []
    for u in users:
        doc_count = db.query(Document).filter(Document.user_id == u.id).count()
        query_count = db.query(ChatMessage)\
            .join(ChatMessage.session)\
            .filter(ChatMessage.role == "user", ChatMessage.session.has(user_id=u.id))\
            .count()
            
        users_summary.append({
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at.isoformat(),
            "document_count": doc_count,
            "query_count": query_count
        })
        
    system_stats = {
        "chroma_chunks": chroma_chunks,
        "upload_dir_size_mb": upload_size_mb,
        "free_disk_space_gb": free_gb,
        "users_list": users_summary
    }
    
    return AdminStats(
        total_users=total_users,
        total_documents=total_documents,
        total_queries=total_queries,
        system_stats=system_stats
    )
