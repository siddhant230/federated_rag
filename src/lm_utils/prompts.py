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
              You are an expert information finder
              ONLY Answer from given context;Do not use prior knowledge or guess, dont mention anything out of the specified information, 
              Be very concise, specific and accurate.
              CONTEXT : {}
              Question: {}
              Answer:
            """
