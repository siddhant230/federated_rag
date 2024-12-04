class InfoRetriever:
    GEMINI_PROMPT = """
              Answer from given context, Be very specific and accurate.
              {}
              Question: {}
              Answer:
            """
    FLAN_T5_PROMPT = """
              Answer from given context, Be very specific and accurate.
              {}
              Question: {}
              Answer:
            """
