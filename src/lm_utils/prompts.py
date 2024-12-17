class InfoRetriever:
    GEMINI_PROMPT = """
              Answer from given context, Be very specific and accurate.
              CONTEXT : {}
              Question: {}
              Answer:
            """
    FLAN_T5_PROMPT = """
              Answer from given context, Be very specific and accurate.
              CONTEXT : {}
              Question: {}
              Answer:
            """
    OLLAMA_QWEN_PROMPT = """
              ONLY Answer from given context, dont mention anything out of the specified information, Be very specific and accurate.
              CONTEXT : {}
              Question: {}
              Answer:
            """
