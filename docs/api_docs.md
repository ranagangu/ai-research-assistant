# API Documentation - AI Research Assistant

This document outlines all backend REST API endpoints available in the AI Research Assistant application. All endpoints except registration and login require a valid JWT bearer token.

## Authentication (`/api/auth`)

### 1. Register User
- **Endpoint**: `POST /api/auth/register`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "role": "admin",
    "created_at": "2026-06-17T12:00:00Z"
  }
  ```
  *(Note: The very first registered user will automatically be assigned the `admin` role for easier stats testing)*

### 2. Login
- **Endpoint**: `POST /api/auth/login`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

### 3. Get Current User Profile
- **Endpoint**: `GET /api/auth/me`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "role": "admin",
    "created_at": "2026-06-17T12:00:00Z"
  }
  ```

---

## Document Management (`/api/documents`)

### 1. Upload Document
- **Endpoint**: `POST /api/documents/upload`
- **Auth Required**: Yes (Bearer Token)
- **Request Body**: `multipart/form-data` containing a `file` field (PDF, DOCX, TXT max 10MB)
- **Response** (201 Created):
  ```json
  {
    "id": "e8a719c2-55db-44b7-87cf-9cbfb9d6a362",
    "filename": "quantum_physics_notes.pdf",
    "file_type": "pdf",
    "file_size": 204850,
    "status": "uploading",
    "created_at": "2026-06-17T12:05:00Z"
  }
  ```
  *(Triggers background extraction, chunking, and vector ingestion)*

### 2. List Documents
- **Endpoint**: `GET /api/documents`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  [
    {
      "id": "e8a719c2-55db-44b7-87cf-9cbfb9d6a362",
      "filename": "quantum_physics_notes.pdf",
      "file_type": "pdf",
      "file_size": 204850,
      "status": "indexed",
      "created_at": "2026-06-17T12:05:00Z"
    }
  ]
  ```

### 3. Delete Document
- **Endpoint**: `DELETE /api/documents/{document_id}`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  {
    "message": "Document successfully deleted"
  }
  ```
  *(Deletes raw file from local storage and related chunks from ChromaDB)*

### 4. Summarize Document
- **Endpoint**: `POST /api/documents/{document_id}/summarize`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  {
    "summary": "This document covers quantum tunneling and wave-particle duality..."
  }
  ```

### 5. Extract Document Keywords
- **Endpoint**: `POST /api/documents/{document_id}/keywords`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  {
    "keywords": ["Quantum", "Physics", "Mechanics", "Tunneling"]
  }
  ```

### 6. Generate Review Questions
- **Endpoint**: `POST /api/documents/{document_id}/questions`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  {
    "questions": [
      "Explain the phenomenon of quantum tunneling.",
      "How is the wave function related to probability amplitude?"
    ]
  }
  ```

---

## Chat RAG Workspace (`/api/chat`)

### 1. Create Chat Session
- **Endpoint**: `POST /api/chat/sessions`
- **Auth Required**: Yes (Bearer Token)
- **Request Body** (Optional):
  ```json
  {
    "title": "Quantum Mechanics Discussion"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "id": "d09a25b2-38ef-466d-8bc4-9d0a6bb8c48a",
    "title": "Quantum Mechanics Discussion",
    "created_at": "2026-06-17T12:10:00Z"
  }
  ```

### 2. List Chat Sessions
- **Endpoint**: `GET /api/chat/sessions`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  [
    {
      "id": "d09a25b2-38ef-466d-8bc4-9d0a6bb8c48a",
      "title": "Quantum Mechanics Discussion",
      "created_at": "2026-06-17T12:10:00Z"
    }
  ]
  ```

### 3. Get Session Details (Messages History)
- **Endpoint**: `GET /api/chat/sessions/{session_id}`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  {
    "id": "d09a25b2-38ef-466d-8bc4-9d0a6bb8c48a",
    "title": "Quantum Mechanics Discussion",
    "created_at": "2026-06-17T12:10:00Z",
    "messages": [
      {
        "id": "m1",
        "session_id": "d09a25b2-38ef-466d-8bc4-9d0a6bb8c48a",
        "role": "user",
        "content": "What is quantum tunneling?",
        "sources": null,
        "created_at": "2026-06-17T12:11:00Z"
      },
      {
        "id": "m2",
        "session_id": "d09a25b2-38ef-466d-8bc4-9d0a6bb8c48a",
        "role": "assistant",
        "content": "Quantum tunneling is a quantum mechanical phenomenon...",
        "sources": [
          {
            "document_id": "e8a719c2-55db-44b7-87cf-9cbfb9d6a362",
            "filename": "quantum_physics_notes.pdf",
            "chunk_index": 2,
            "text": "Quantum tunneling represents the probability..."
          }
        ],
        "created_at": "2026-06-17T12:11:05Z"
      }
    ]
  }
  ```

### 4. Delete Chat Session
- **Endpoint**: `DELETE /api/chat/sessions/{session_id}`
- **Auth Required**: Yes (Bearer Token)
- **Response** (200 OK):
  ```json
  {
    "message": "Session deleted successfully"
  }
  ```

### 5. Query Session (Sync)
- **Endpoint**: `POST /api/chat/sessions/{session_id}/query`
- **Auth Required**: Yes (Bearer Token)
- **Request Body**:
  ```json
  {
    "content": "Does my physics notes talk about tunneling?"
  }
  ```
- **Response** (200 OK):
  Returns assistant message containing citation arrays.

### 6. Query Session (Stream)
- **Endpoint**: `GET /api/chat/sessions/{session_id}/query/stream`
- **Auth Required**: Yes (Can send token as parameter `?token=XYZ` or Authorization Header)
- **Query Parameters**:
  - `q`: The query text
  - `token`: The JWT bearer token (used for browser EventSource SSE connections)
- **Response**: Server-Sent Events stream (`text/event-stream`).
  - Event payload format (JSON string):
    ```json
    // Yielded token chunk
    {"type": "token", "content": "Quantum "}
    
    // Finished signal containing final citations
    {"type": "done", "message_id": "assistant_msg_uuid", "sources": [{"filename": "doc.pdf", "chunk_index": 0}]}
    ```

---

## Admin Analytics Dashboard (`/api/admin`)

### 1. System Usage Stats
- **Endpoint**: `GET /api/admin/stats`
- **Auth Required**: Yes (Bearer Token with `admin` role)
- **Response** (200 OK):
  ```json
  {
    "total_users": 5,
    "total_documents": 22,
    "total_queries": 450,
    "system_stats": {
      "chroma_chunks": 1240,
      "upload_dir_size_mb": 14.5,
      "free_disk_space_gb": 120.4,
      "users_list": [
        {
          "id": 1,
          "email": "admin@example.com",
          "role": "admin",
          "created_at": "2026-06-17T12:00:00Z",
          "document_count": 4,
          "query_count": 25
        }
      ]
    }
  }
  ```
