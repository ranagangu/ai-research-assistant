import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from backend.database.session import get_db, SessionLocal
from backend.models.db_models import User, Document
from backend.models.schema_models import DocumentOut, SummaryResponse, KeywordsResponse, QuestionsResponse
from backend.utils.deps import get_current_user
from backend.config.settings import settings
from backend.services.doc_processor import DocumentProcessor
from backend.services.vector_store import VectorStoreService
from backend.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Supported file extensions
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""

def process_document_background(doc_id: str, filepath: str, filename: str, file_type: str, user_id: int):
    """
    Background worker to extract text, chunk it, and index it into ChromaDB.
    """
    db = SessionLocal()
    try:
        logger.info(f"Background process starting for document: {doc_id}")
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            logger.error(f"Document {doc_id} not found in database.")
            return

        doc.status = "processing"
        db.commit()

        # 1. Extract raw text
        text = DocumentProcessor.extract_text(filepath, file_type)
        if not text.strip():
            raise ValueError("No text could be extracted from the document.")

        # 2. Chunk text
        chunks = DocumentProcessor.chunk_text(text)

        # 3. Embed and store in ChromaDB
        vector_service = VectorStoreService()
        vector_service.add_document_chunks(
            document_id=doc_id,
            user_id=user_id,
            filename=filename,
            chunks=chunks
        )

        # 4. Index successfully completed
        doc.status = "indexed"
        db.commit()
        logger.info(f"Background indexing completed for document: {doc_id}")
    except Exception as e:
        logger.error(f"Failed background indexing for document {doc_id}: {str(e)}")
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, DOCX, TXT) and trigger background ingestion.
    """
    filename = file.filename
    ext = get_file_extension(filename)
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    # Generate random unique filename on disk to avoid conflicts
    unique_filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save the file to local disk
    try:
        with open(filepath, "wb") as f:
            f.write(file.file.read())
    except Exception as e:
        logger.error(f"Error saving uploaded file to disk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file."
        )
        
    # Create database entry
    db_doc = Document(
        filename=filename,
        filepath=filepath,
        file_type=ext,
        file_size=os.path.getsize(filepath),
        status="uploading",
        user_id=current_user.id
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Trigger background text extraction and vector indexing
    background_tasks.add_task(
        process_document_background,
        doc_id=db_doc.id,
        filepath=filepath,
        filename=filename,
        file_type=ext,
        user_id=current_user.id
    )
    
    return db_doc


@router.get("", response_model=List[DocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve list of uploaded documents for the active user.
    """
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()
    return docs


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document, clean up disk storage, and purge indices in ChromaDB.
    """
    doc = db.query(Document).filter(
        Document.id == document_id, 
        Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
        
    # 1. Delete file from local disk
    if os.path.exists(doc.filepath):
        try:
            os.remove(doc.filepath)
        except Exception as e:
            logger.error(f"Error removing file from disk: {str(e)}")
            
    # 2. Delete vectors from ChromaDB
    try:
        vector_service = VectorStoreService()
        vector_service.delete_document(document_id=doc.id, user_id=current_user.id)
    except Exception as e:
        logger.error(f"Error removing vectors from Chroma: {str(e)}")
        # Continue with SQL delete even if Chroma delete fails, to keep state clean
        
    # 3. Delete from DB
    db.delete(doc)
    db.commit()
    
    return {"message": "Document successfully deleted"}


# AI Operations on Documents
@router.post("/{document_id}/summarize", response_model=SummaryResponse)
def summarize_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve full text and generate a structured summary.
    """
    doc = db.query(Document).filter(
        Document.id == document_id, 
        Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if doc.status != "indexed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document is not fully processed yet.")
        
    try:
        text = DocumentProcessor.extract_text(doc.filepath, doc.file_type)
        ai_service = AIService()
        summary = ai_service.summarize_text(text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Summary failed: {str(e)}")


@router.post("/{document_id}/keywords", response_model=KeywordsResponse)
def extract_document_keywords(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze text and extract key metadata terms.
    """
    doc = db.query(Document).filter(
        Document.id == document_id, 
        Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if doc.status != "indexed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document is not fully processed yet.")
        
    try:
        text = DocumentProcessor.extract_text(doc.filepath, doc.file_type)
        ai_service = AIService()
        keywords = ai_service.extract_keywords(text)
        return {"keywords": keywords}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Keyword extraction failed: {str(e)}")


@router.post("/{document_id}/questions", response_model=QuestionsResponse)
def generate_document_questions(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate sample review questions from document content.
    """
    doc = db.query(Document).filter(
        Document.id == document_id, 
        Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if doc.status != "indexed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document is not fully processed yet.")
        
    try:
        text = DocumentProcessor.extract_text(doc.filepath, doc.file_type)
        ai_service = AIService()
        questions = ai_service.generate_questions(text)
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Questions generation failed: {str(e)}")
