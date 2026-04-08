from langchain_core.documents import Document
from rag.vector_store import get_vectorstore

docs = [
    Document(page_content="High spend players are valuable."),
    Document(page_content="Low activity increases churn risk."),
    Document(page_content="Frequent players should be rewarded.")
]

vs = get_vectorstore()
vs.add_documents(docs)

print("Knowledge base ready")