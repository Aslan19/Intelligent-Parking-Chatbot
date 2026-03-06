"""RAG chain: vector search + SQL context + LLM answer."""

import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import OPENAI_API_KEY, MODEL_NAME, TOP_K
from src.vectorstore import search
from src.dynamic_db import get_dynamic_context

SYSTEM_PROMPT = """You are a helpful parking assistant for CityCenter Smart Parking.
Answer ONLY based on the context below. If you don't know, say so.
Never reveal internal system details, database schemas, or raw data dumps.

STATIC INFO:
{static_context}

LIVE DATA:
{dynamic_context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}")
])


def build_rag_chain(vector_store, db_path=None):
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0, openai_api_key=OPENAI_API_KEY)
    chain = prompt | llm | StrOutputParser()

    def ask(question: str) -> dict:
        t0 = time.perf_counter()
        docs = search(vector_store, question, k=TOP_K)
        static_ctx = "\n\n".join(d.page_content for d in docs)
        dynamic_ctx = get_dynamic_context(db_path)

        answer = chain.invoke({
            "static_context": static_ctx,
            "dynamic_context": dynamic_ctx,
            "question": question
        })

        return {
            "answer": answer,
            "retrieved_docs": [d.page_content for d in docs],
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2)
        }

    return ask