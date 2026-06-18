from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # Core inputs/context
    query: str
    chat_history: List[Dict[str, str]]
    user_id: int
    session_id: str
    model_provider: str
    
    # Node outputs
    analysis: Dict[str, Any]
    retrieved_docs: List[Dict[str, Any]]
    relevant_docs: List[Dict[str, Any]]
    answer: str
    citations: List[Dict[str, Any]]
    
    # Validation flags
    hallucination_grade: str  # 'yes' (hallucinated) or 'no' (grounded)
    answers_query_grade: str  # 'yes' (satisfies query) or 'no' (fails query)
    retry_count: int
