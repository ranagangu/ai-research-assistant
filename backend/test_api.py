import unittest
import os
import sys
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current workspace to path to allow importing backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.session import Base
from backend.models.db_models import User, Document, ChatSession, ChatMessage
from backend.utils.deps import create_access_token
from jose import jwt
from backend.config.settings import settings

class TestResearchAssistantBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up a temporary test SQLite database
        cls.test_db_url = "sqlite:///./test_research_assistant.db"
        cls.engine = create_engine(cls.test_db_url, connect_args={"check_same_thread": False})
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Create tables
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        # Clean up database file
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()
        if os.path.exists("./test_research_assistant.db"):
            try:
                os.remove("./test_research_assistant.db")
            except Exception:
                pass

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_user_creation_and_password_hashing(self):
        """
        Verify that user passwords are encrypted correctly and verification succeeds.
        """
        email = f"test_{uuid.uuid4()}@example.com"
        password = "secure_password_123"
        
        hashed = User.hash_password(password)
        user = User(email=email, hashed_password=hashed, role="user")
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Verify user is inserted
        db_user = self.db.query(User).filter(User.email == email).first()
        self.assertIsNotNone(db_user)
        self.assertTrue(db_user.verify_password(password))
        self.assertFalse(db_user.verify_password("wrong_password"))

    def test_jwt_token_mechanics(self):
        """
        Verify access token generation and field decoding.
        """
        email = "jwt_test@example.com"
        user_id = 999
        role = "admin"
        
        token = create_access_token(
            data={"sub": email, "id": user_id, "role": role},
            expires_delta=datetime.timedelta(minutes=15)
        )
        
        # Decode and verify fields
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        self.assertEqual(payload.get("sub"), email)
        self.assertEqual(payload.get("id"), user_id)
        self.assertEqual(payload.get("role"), role)

    def test_document_model_crud(self):
        """
        Verify document registration and user relationships.
        """
        # Create User
        user = User(email="doc_user@example.com", hashed_password="hashed_placeholder")
        self.db.add(user)
        self.db.commit()
        
        # Create Document referencing User
        doc_id = str(uuid.uuid4())
        doc = Document(
            id=doc_id,
            filename="paper.pdf",
            filepath="/tmp/paper.pdf",
            file_type="pdf",
            file_size=54200,
            status="uploading",
            user_id=user.id
        )
        self.db.add(doc)
        self.db.commit()
        
        # Verify persistence and back_populates relationship
        db_doc = self.db.query(Document).filter(Document.id == doc_id).first()
        self.assertIsNotNone(db_doc)
        self.assertEqual(db_doc.filename, "paper.pdf")
        self.assertEqual(db_doc.user.email, "doc_user@example.com")

    def test_chat_session_and_message_cascade(self):
        """
        Verify that chat sessions hold messages and properly cascade delete.
        """
        user = User(email="chat_user@example.com", hashed_password="hashed_placeholder")
        self.db.add(user)
        self.db.commit()
        
        # Create Session
        session_id = str(uuid.uuid4())
        session = ChatSession(id=session_id, title="RAG Session", user_id=user.id)
        self.db.add(session)
        self.db.commit()
        
        # Add messages
        msg_user = ChatMessage(session_id=session_id, role="user", content="Hello RAG")
        msg_assistant = ChatMessage(session_id=session_id, role="assistant", content="Hello User")
        self.db.add_all([msg_user, msg_assistant])
        self.db.commit()
        
        # Check messages count
        db_session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        self.assertEqual(len(db_session.messages), 2)
        
        # Delete session and verify message cascades
        self.db.delete(db_session)
        self.db.commit()
        
        orphaned_msgs = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        self.assertEqual(len(orphaned_msgs), 0)

if __name__ == '__main__':
    unittest.main()
