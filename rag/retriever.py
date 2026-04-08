def retrieve_context(vs, query):
    docs = vs.similarity_search(query, k=2)
    return "\n".join([d.page_content for d in docs])