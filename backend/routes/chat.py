from backend.config.settings import settings as app_settings
from backend.models.schema_models import ChatSessionCreate
import json
import logging
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.models.db_models import User, ChatSession, ChatMessage
from backend.models.schema_models import ChatSessionOut, ChatSessionDetail, MessageOut, MessageCreate
from backend.utils.deps import get_current_user
from backend.graph.workflow import compile_workflow

print("Settings object:", app_settings)
print("Default provider:", app_settings.DEFAULT_LLM_PROVIDER)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

workflow_app = compile_workflow()

@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    session_in: ChatSessionCreate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new chat session.
    """
    title = (session_in.title if session_in else "New Research Session") or "New Research Session"
    session = ChatSession(
        title=title,
        user_id=current_user.id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=List[ChatSessionOut])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all chat sessions for the active user.
    """
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve session details including full message history.
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a chat session and all its message logs.
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
        
    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}


@router.post("/sessions/{session_id}/query", response_model=MessageOut)
def query_session(
    session_id: str,
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute RAG workflow on user query and return answer (Synchronous endpoint).
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_in.content
    )
    db.add(user_msg)
    db.commit()
    
    # Get chat history for the graph
    history_list = []
    # session.messages is sorted by created_at. Exclude the user message we just added
    for msg in session.messages[:-1]:
        history_list.append({"role": msg.role, "content": msg.content})
        
    # Run LangGraph RAG Agent Workflow
    initial_state = {
        "query": message_in.content,
        "chat_history": history_list,
        "user_id": current_user.id,
        "session_id": session_id,
        "model_provider": app_settings.DEFAULT_LLM_PROVIDER,
        "retry_count": 0
    }
    
    try:
        result_state = workflow_app.invoke(initial_state)
        answer = result_state.get("answer", "No answer could be generated.")
        citations = result_state.get("citations", [])
    except Exception as e:
        logger.error(f"Error executing LangGraph: {str(e)}")
        answer = f"Error during query execution: {str(e)}"
        citations = []
        
    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        sources=json.dumps(citations)
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    
    # Format message out with parsed sources JSON
    msg_out = MessageOut(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        sources=citations,
        created_at=assistant_msg.created_at
    )
    return msg_out


@router.get("/sessions/{session_id}/query/stream")
def query_session_stream(
    session_id: str,
    q: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Execute RAG workflow and stream response text using Server-Sent Events (SSE).
    Supports token validation via query param 'token' for SSE EventSource clients.
    """
    from backend.utils.deps import get_current_user
    
    current_user = get_current_user(db=db, token=None, token_query=token)
    
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Save User message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=q
    )
    db.add(user_msg)
    db.commit()
    
    # Get history
    history_list = []
    for msg in session.messages[:-1]:
        history_list.append({"role": msg.role, "content": msg.content})

    async def event_generator():
        # First, run the LangGraph workflow to retrieve, evaluate and generate final text
        # Since graph invocation is synchronous, run it in an executor to keep it async friendly
        initial_state = {
            "query": q,
            "chat_history": history_list,
            "user_id": current_user.id,
            "session_id": session_id,
            "model_provider": app_settings.DEFAULT_LLM_PROVIDER,
            "retry_count": 0
        }
        
        loop = asyncio.get_event_loop()
        try:
            # Execute graph invocation in a threadpool executor to avoid blocking the async event loop
            result_state = await loop.run_in_executor(None, lambda: workflow_app.invoke(initial_state))
            answer = result_state.get("answer", "No answer could be generated.")
            citations = result_state.get("citations", [])
        except Exception as e:
            logger.error(f"Error executing LangGraph: {e}")
            answer = f"Error during query execution: {str(e)}"
            citations = []
            
        # Stream the tokens (words) to simulate typing effect or stream actual response chunks
        words = answer.split(" ")
        for i, word in enumerate(words):
            chunk = (word + " ") if i < len(words) - 1 else word
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
            await asyncio.sleep(0.03)  # smooth typing flow
            
        # Write response to DB using a fresh session to avoid closed-session issues in async generator
        from backend.database.session import SessionLocal
        db_session = SessionLocal()
        assistant_msg_id = None
        try:
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=answer,
                sources=json.dumps(citations)
            )
            db_session.add(assistant_msg)
            db_session.commit()
            db_session.refresh(assistant_msg)
            assistant_msg_id = assistant_msg.id
        except Exception as db_err:
            logger.error(f"Database error saving assistant message: {db_err}")
            db_session.rollback()
        finally:
            db_session.close()
        
        # Send termination data with ID and Citations
        yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_msg_id, 'sources': citations})}\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")
