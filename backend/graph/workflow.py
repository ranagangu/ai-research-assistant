import json
import logging
from typing import List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from backend.config.settings import settings
from backend.graph.state import AgentState
from backend.services.ai_service import get_llm
from backend.services.vector_store import VectorStoreService
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

# Helper to run validation LLM calls
def create_grader_chain(llm, prompt_template: str):
    prompt = ChatPromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()

class RAGWorkflow:
    def __init__(self):
        # We will dynamically get LLM inside nodes based on state settings to avoid static startup failures
        pass

    @staticmethod
    def analyze_query(state: AgentState) -> Dict[str, Any]:
        """
        Node: Analyzes user query, decides if retrieval is necessary, and reformulates query.
        """
        logger.info(f"Node: Analyze Query - {state['query']}")
        query = state["query"]
        provider = state.get("model_provider") or settings.DEFAULT_LLM_PROVIDER
        
        try:
            llm = get_llm(provider, temperature=0.1)
            
            prompt = ChatPromptTemplate.from_template(
                "You are an AI Research Query Analyzer.\n"
                "Analyze the user's research query in the context of chat history.\n"
                "Determine:\n"
                "1. If document retrieval is needed (is it asking about specific documents, data, or technical facts? or is it a general greeting/conversational phrase? Answer with YES or NO).\n"
                "2. A optimized search query for vector store retrieval.\n"
                "3. Key search terms.\n\n"
                "Chat History:\n{history}\n\n"
                "User Query:\n{query}\n\n"
                "Output your response strictly as a JSON object with keys: 'retrieval_needed' (boolean), 'search_query' (string), and 'keywords' (array of strings)."
            )
            
            # Format history
            hist_str = ""
            for msg in state.get("chat_history", [])[-5:]:  # Last 5 messages
                hist_str += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"
            
            chain = prompt | llm | StrOutputParser()
            res = chain.invoke({"query": query, "history": hist_str})
            
            # Parse JSON
            try:
                # Clean code block indicators if any
                clean_res = res.strip().replace("```json", "").replace("```", "").strip()
                analysis = json.loads(clean_res)
            except Exception:
                # Fallback if LLM output is not valid JSON
                analysis = {
                    "retrieval_needed": True,
                    "search_query": query,
                    "keywords": []
                }
        except Exception as e:
            logger.error(f"Error in analyze_query node: {e}")
            analysis = {
                "retrieval_needed": True,
                "search_query": query,
                "keywords": []
            }
            
        return {"analysis": analysis, "retry_count": state.get("retry_count", 0)}

    @staticmethod
    def retrieve_docs(state: AgentState) -> Dict[str, Any]:
        """
        Node: Retrieves documents from vector store.
        """
        logger.info("Node: Retrieve Documents")
        analysis = state["analysis"]
        user_id = state["user_id"]
        
        if not analysis.get("retrieval_needed", True):
            logger.info("Retrieval not needed based on analysis.")
            return {"retrieved_docs": []}
            
        search_query = analysis.get("search_query", state["query"])
        
        try:
            vector_service = VectorStoreService(provider=state.get("model_provider"))
            retrieved = vector_service.search_similar(search_query, user_id=user_id, top_k=5)
            logger.info(f"Retrieved {len(retrieved)} chunks from ChromaDB.")
        except Exception as e:
            logger.error(f"Error in retrieve_docs node: {e}")
            retrieved = []
            
        return {"retrieved_docs": retrieved}

    @staticmethod
    def evaluate_context(state: AgentState) -> Dict[str, Any]:
        """
        Node: Evaluates retrieved documents relevance to query.
        """
        logger.info("Node: Evaluate Context")
        retrieved_docs = state.get("retrieved_docs", [])
        query = state["query"]
        provider = state.get("model_provider") or settings.DEFAULT_LLM_PROVIDER
        
        if not retrieved_docs:
            return {"relevant_docs": []}
            
        try:
            llm = get_llm(provider, temperature=0.0)
            grader_prompt = (
                "You are an expert document grader. You need to grade the relevance of a retrieved document chunk to a user's question.\n"
                "If the document chunk contains information relevant to the question, grade it as 'yes'. Otherwise, grade it as 'no'.\n"
                "Do not write anything else, only output 'yes' or 'no'.\n\n"
                "Document Chunk:\n{context}\n\n"
                "User Question:\n{query}\n\n"
                "Grade:"
            )
            grader_chain = create_grader_chain(llm, grader_prompt)
            
            relevant_docs = []
            for doc in retrieved_docs:
                grade = grader_chain.invoke({"context": doc["text"], "query": query}).strip().lower()
                if "yes" in grade:
                    relevant_docs.append(doc)
            
            logger.info(f"Evaluated documents. Relevant count: {len(relevant_docs)} / {len(retrieved_docs)}")
            return {"relevant_docs": relevant_docs}
        except Exception as e:
            logger.error(f"Error in evaluate_context node: {e}")
            # Fallback: keep all documents
            return {"relevant_docs": retrieved_docs}

    @staticmethod
    def generate_answer(state: AgentState) -> Dict[str, Any]:
        """
        Node: Generates the answer based on query, relevant docs and history.
        """
        logger.info("Node: Generate Answer")
        query = state["query"]
        relevant_docs = state.get("relevant_docs", [])
        provider = state.get("model_provider") or settings.DEFAULT_LLM_PROVIDER
        
        # Build Context String
        context_str = ""
        citations = []
        for doc in relevant_docs:
            meta = doc.get("metadata", {})
            filename = meta.get("filename", "Unknown Document")
            chunk_idx = meta.get("chunk_index", 0)
            doc_id = meta.get("document_id", "")
            
            # Format internal reference tag
            ref_tag = f"[{filename} (Chunk {chunk_idx})]"
            context_str += f"Source: {ref_tag}\nContent:\n{doc['text']}\n\n"
            
            citations.append({
                "document_id": doc_id,
                "filename": filename,
                "chunk_index": chunk_idx,
                "text": doc["text"][:300] + "..."  # Snippet for frontend
            })
            
        try:
            llm = get_llm(provider, temperature=0.3)
            
            if not context_str:
                # Generate answer without context or ask for documents if it requires them
                prompt = ChatPromptTemplate.from_template(
                    "You are an AI Research Assistant.\n"
                    "The user is asking a general question, or there are no uploaded reference documents matching their query.\n"
                    "If they are asking about specific files, politely remind them to upload documents in the Document Center first.\n"
                    "Otherwise, answer their question to the best of your ability using your general knowledge.\n\n"
                    "Chat History:\n{history}\n\n"
                    "Question:\n{query}\n\n"
                    "Answer:"
                )
            else:
                prompt = ChatPromptTemplate.from_template(
                    "You are an AI Research Assistant. Answer the question using the provided context chunks. "
                    "Make sure to cite your sources using the source tags (e.g. [Filename (Chunk X)]) inline where you refer to that information.\n"
                    "Stay strictly grounded in the provided context. Do not make up facts or extrapolate beyond what is documented in the context.\n\n"
                    "Context Chunks:\n{context}\n\n"
                    "Chat History:\n{history}\n\n"
                    "Question:\n{query}\n\n"
                    "Answer with citations:"
                )
            
            hist_str = ""
            for msg in state.get("chat_history", [])[-5:]:
                hist_str += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"
                
            chain = prompt | llm | StrOutputParser()
            
            inputs = {"history": hist_str, "query": query}
            if context_str:
                inputs["context"] = context_str
                
            answer = chain.invoke(inputs)
            return {"answer": answer, "citations": citations}
        except Exception as e:
            logger.error(f"Error in generate_answer node: {e}")
            return {"answer": f"An error occurred while generating answer: {str(e)}", "citations": []}

    @staticmethod
    def validate_response(state: AgentState) -> Dict[str, Any]:
        """
        Node: Validates the generated answer for grounding (hallucination) and topic accuracy.
        """
        logger.info("Node: Validate Response")
        relevant_docs = state.get("relevant_docs", [])
        answer = state["answer"]
        query = state["query"]
        provider = state.get("model_provider") or settings.DEFAULT_LLM_PROVIDER
        
        # If no documents were retrieved/relevant, we skip grounding checks
        if not relevant_docs:
            return {
                "hallucination_grade": "no",  # not hallucinated because no docs to ground in
                "answers_query_grade": "yes",
                "retry_count": state.get("retry_count", 0)
            }
            
        try:
            llm = get_llm(provider, temperature=0.0)
            
            # Grounding check prompt
            grounding_prompt = (
                "You are an expert validator checking if an answer is hallucinated.\n"
                "Check if the generated response is fully grounded in and supported by the retrieved document context. "
                "Evaluate facts. If the answer contains statements NOT supported by the context, grade it as 'yes' (it has hallucination).\n"
                "If it is fully supported and makes no outside assumptions, grade it as 'no' (it has NO hallucination).\n"
                "Do not write anything else, only output 'yes' or 'no'.\n\n"
                "Retrieved Context:\n{context}\n\n"
                "Generated Response:\n{answer}\n\n"
                "Grade (yes/no):"
            )
            
            # Query answer check prompt
            query_answer_prompt = (
                "You are an expert validator checking if an answer successfully addresses a user's question.\n"
                "Does the generated response answer the user's question? If it is helpful and answers the question, grade it as 'yes'.\n"
                "Otherwise, grade it as 'no'.\n"
                "Do not write anything else, only output 'yes' or 'no'.\n\n"
                "User Question:\n{query}\n\n"
                "Generated Response:\n{answer}\n\n"
                "Grade (yes/no):"
            )
            
            context_str = "\n\n".join([doc["text"] for doc in relevant_docs])
            
            grounding_grader = create_grader_chain(llm, grounding_prompt)
            query_grader = create_grader_chain(llm, query_answer_prompt)
            
            hallucination_grade = grounding_grader.invoke({"context": context_str, "answer": answer}).strip().lower()
            answers_query_grade = query_grader.invoke({"query": query, "answer": answer}).strip().lower()
            
            # Normalize outputs
            hallucination_grade = "yes" if "yes" in hallucination_grade else "no"
            answers_query_grade = "yes" if "yes" in answers_query_grade else "no"
            
            logger.info(f"Validation grades: Hallucination={hallucination_grade}, AnswersQuery={answers_query_grade}")
            
            return {
                "hallucination_grade": hallucination_grade,
                "answers_query_grade": answers_query_grade,
                "retry_count": state.get("retry_count", 0)
            }
        except Exception as e:
            logger.error(f"Error in validate_response node: {e}")
            return {
                "hallucination_grade": "no",
                "answers_query_grade": "yes",
                "retry_count": state.get("retry_count", 0)
            }

    @staticmethod
    def regenerate_node(state: AgentState) -> Dict[str, Any]:
        """
        Node: Increments retry counter and provides instruction to re-generate.
        """
        retries = state.get("retry_count", 0) + 1
        logger.info(f"Node: Incrementing retries to {retries}")
        return {"retry_count": retries}


def route_validation(state: AgentState) -> Literal["regenerate", "end"]:
    """
    Decides routing based on validation grades.
    """
    hallucination = state.get("hallucination_grade", "no")
    answers_query = state.get("answers_query_grade", "yes")
    retries = state.get("retry_count", 0)
    
    if (hallucination == "yes" or answers_query == "no") and retries < 2:
        logger.info("Validation failed. Routing to regenerate node.")
        return "regenerate"
        
    logger.info("Validation passed or retry limit exceeded. Routing to end.")
    return "end"


def compile_workflow():
    """
    Assembles and compiles the StateGraph workflow.
    """
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("analyze_query", RAGWorkflow.analyze_query)
    workflow.add_node("retrieve_docs", RAGWorkflow.retrieve_docs)
    workflow.add_node("evaluate_context", RAGWorkflow.evaluate_context)
    workflow.add_node("generate_answer", RAGWorkflow.generate_answer)
    workflow.add_node("validate_response", RAGWorkflow.validate_response)
    workflow.add_node("regenerate", RAGWorkflow.regenerate_node)
    
    # Define Transitions
    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "retrieve_docs")
    workflow.add_edge("retrieve_docs", "evaluate_context")
    workflow.add_edge("evaluate_context", "generate_answer")
    workflow.add_edge("generate_answer", "validate_response")
    
    # Conditional Routing
    workflow.add_conditional_edges(
        "validate_response",
        route_validation,
        {
            "regenerate": "regenerate",
            "end": END
        }
    )
    
    # From regenerate, loop back to generate
    # We can rewrite query, but looping to generate_answer with stricter instructions is very fast and efficient.
    # Let's map regenerate directly to generate_answer.
    workflow.add_edge("regenerate", "generate_answer")
    
    return workflow.compile()
