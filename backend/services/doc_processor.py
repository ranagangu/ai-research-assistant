import os
import pypdf
import docx
import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentProcessor:
    @staticmethod
    def extract_text(filepath: str, file_type: str) -> str:
        """
        Extracts raw text from PDF, DOCX, or TXT file.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found at: {filepath}")
        
        text = ""
        file_type = file_type.lower()
        
        try:
            if file_type == "pdf":
                reader = pypdf.PdfReader(filepath)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            elif file_type in ["docx", "doc"]:
                doc = docx.Document(filepath)
                for paragraph in doc.paragraphs:
                    if paragraph.text:
                        text += paragraph.text + "\n"
            elif file_type == "txt":
                # Try UTF-8 first, fallback to Latin-1
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                except UnicodeDecodeError:
                    with open(filepath, "r", encoding="latin-1") as f:
                        text = f.read()
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {filepath}: {str(e)}")
            raise e
            
        return text

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Chunks text into structured items using RecursiveCharacterTextSplitter.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = splitter.split_text(text)
        chunked_docs = []
        for i, chunk in enumerate(chunks):
            chunked_docs.append({
                "text": chunk,
                "chunk_index": i
            })
            
        return chunked_docs
