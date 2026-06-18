import os
import logging
import chromadb
from typing import List, Dict, Any, Optional
from backend.config.settings import settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Global client initialization
_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
    return _chroma_client

def get_embeddings(provider: Optional[str] = None):
    provider = provider or settings.DEFAULT_EMBEDDING_PROVIDER
    
    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not configured in environment variables.")
        return OpenAIEmbeddings(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            model=settings.DEFAULT_EMBEDDING_MODEL
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


class VectorStoreService:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.DEFAULT_EMBEDDING_PROVIDER
        self.client = get_chroma_client()
        self.collection_name = "document_chunks"

    def _get_vectorstore(self) -> Chroma:
        embeddings = get_embeddings(self.provider)
        return Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=embeddings
        )

    def add_document_chunks(self, document_id: str, user_id: int, filename: str, chunks: List[Dict[str, Any]]) -> bool:
        """
        Adds text chunks to ChromaDB.
        """
        try:
            vectorstore = self._get_vectorstore()
            
            docs = []
            for chunk in chunks:
                doc = Document(
                    page_content=chunk["text"],
                    metadata={
                        "document_id": str(document_id),
                        "user_id": int(user_id),
                        "filename": str(filename),
                        "chunk_index": int(chunk["chunk_index"])
                    }
                )
                docs.append(doc)
            
            vectorstore.add_documents(docs)
            logger.info(f"Successfully added {len(chunks)} chunks to Chroma for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding chunks to Chroma: {str(e)}")
            raise e

    def search_similar(self, query: str, user_id: int, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches ChromaDB for matching chunks filtering by user_id.
        """
        try:
            vectorstore = self._get_vectorstore()
            
            # Perform similarity search with user_id filter
            search_results = vectorstore.similarity_search_with_relevance_scores(
                query,
                k=top_k,
                filter={"user_id": int(user_id)}
            )
            
            formatted_results = []
            for doc, score in search_results:
                formatted_results.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
                
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return []

    def delete_document(self, document_id: str, user_id: int) -> bool:
        """
        Deletes all chunks associated with document_id and user_id.
        """
        try:
            # We can use direct client collection interaction for precise deletion
            collection = self.client.get_or_create_collection(self.collection_name)
            
            # Find and delete where document_id matches
            # Chroma supports deleting by metadata filters
            collection.delete(
                where={
                    "$and": [
                        {"document_id": str(document_id)},
                        {"user_id": int(user_id)}
                    ]
                }
            )
            logger.info(f"Deleted chunks for document {document_id} of user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chunks from Chroma: {str(e)}")
            raise e
            
    def get_user_chunks_count(self, user_id: int) -> int:
        """
        Count total chunks stored for user_id.
        """
        try:
            collection = self.client.get_or_create_collection(self.collection_name)
            results = collection.get(
                where={"user_id": int(user_id)},
                include=[]
            )
            return len(results["ids"]) if results else 0
        except Exception:
            return 0
            
    def get_total_chunks_count(self) -> int:
        """
        Count total chunks stored across all users.
        """
        try:
            collection = self.client.get_or_create_collection(self.collection_name)
            return collection.count()
        except Exception:
            return 0
