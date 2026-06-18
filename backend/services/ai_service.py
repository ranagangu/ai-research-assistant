import os
import logging
from typing import List, Optional

from backend.config.settings import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2
):
    provider = provider or settings.DEFAULT_LLM_PROVIDER
    model = model or settings.DEFAULT_LLM_MODEL

    if provider.lower() == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is not configured in environment variables."
            )

        return ChatOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            model=model,
            temperature=temperature,
            default_headers={
                "HTTP-Referer": "https://ai-research-assistant-d3z9.onrender.com",
                "X-Title": settings.PROJECT_NAME,
            }
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


class AIService:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self.llm = get_llm(self.provider)

    def summarize_text(self, text: str) -> str:
        """
        Summarize document content.
        """
        try:
            sample_text = text[:15000]

            prompt = ChatPromptTemplate.from_template(
                """
You are an expert academic research assistant.

Summarize the following document in a structured format.

Include:
- Main topic
- Key findings
- Important concepts
- Methodology (if applicable)
- Conclusion

Document:
{text}

Summary:
"""
            )

            chain = prompt | self.llm | StrOutputParser()

            result = chain.invoke({
                "text": sample_text
            })

            return result.strip()

        except Exception as e:
            logger.error(f"Error in summarize_text: {str(e)}")
            return f"Failed to generate summary: {str(e)}"

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.
        """
        try:
            sample_text = text[:10000]

            prompt = ChatPromptTemplate.from_template(
                """
Extract 5-10 important keywords from the text below.

Return ONLY a comma-separated list.

Text:
{text}

Keywords:
"""
            )

            chain = prompt | self.llm | StrOutputParser()

            result = chain.invoke({
                "text": sample_text
            })

            keywords = [
                keyword.strip()
                for keyword in result.split(",")
                if keyword.strip()
            ]

            return keywords

        except Exception as e:
            logger.error(f"Error in extract_keywords: {str(e)}")
            return []

    def generate_questions(self, text: str) -> List[str]:
        """
        Generate study/research questions.
        """
        try:
            sample_text = text[:10000]

            prompt = ChatPromptTemplate.from_template(
                """
Based on the following document, generate 5 high-quality questions.

Return one question per line.

Text:
{text}

Questions:
"""
            )

            chain = prompt | self.llm | StrOutputParser()

            result = chain.invoke({
                "text": sample_text
            })

            questions = []

            for line in result.split("\n"):
                line = line.strip()

                if not line:
                    continue

                if (
                    line[0].isdigit()
                    or line.startswith("-")
                    or line.startswith("*")
                ):
                    cleaned = line.lstrip(
                        "0123456789.-* "
                    ).strip()

                    if cleaned:
                        questions.append(cleaned)
                else:
                    questions.append(line)

            return questions[:5]

        except Exception as e:
            logger.error(f"Error in generate_questions: {str(e)}")
            return []