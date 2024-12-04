from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import (
    Settings
)


class BaseEmbeddingModel:
    """
    Abstract class for interfacing any Embedding model.
    To implement any new embedding model, follow the exmaple of BaaiLlamaIndexModel below.
    You need to implement the embed_data method.
    """

    def __init__(self, model_name):
        self.model_name = model_name

    def embed_data(self, data):
        pass


class BgeSmallEmbedModel(BaseEmbeddingModel):
    """
    Assuming llama-index-implementation as base class
    and "BAAI/bge-small-en-v1.5" as default embedding model.
    """

    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        super().__init__(model_name)
        self.embedding_model = HuggingFaceEmbedding(model_name=self.model_name)
        Settings.embed_model = self.embedding_model
        print(self.model_name)

    def embed_data(self, data):
        data_embedding = self.embedding_model.get_query_embedding(data)
        return data_embedding
