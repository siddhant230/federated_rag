import os
import shutil
from pathlib import Path

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext, load_index_from_storage
)
from llama_index.core.composability import ComposableGraph
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.llms.gemini import Gemini


class RagUtilities:
    def __init__(self):
        # local embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5")
        self.llm_predictor = Gemini(
            model="models/gemini-1.5-flash",
            # uses GOOGLE_API_KEY
            api_key=open("config_key.txt").read(),
        )
        self.set_config()

    def set_config(self):
        Settings.embed_model = self.embed_model
        Settings.llm = self.llm_predictor

    def load_from_disk(self, persist_dir):
        # rebuild storage context
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        # load index
        index = load_index_from_storage(storage_context)
        return index

    def index_creator(self, file_path: str, target_path: str):
        doc = SimpleDirectoryReader(input_files=[file_path]).load_data()
        index = VectorStoreIndex.from_documents(doc)
        target_path = Path(target_path) / "vector_index"
        if os.path.exists(target_path):
            shutil.rmtree(target_path)

        index.storage_context.persist(persist_dir=target_path)
        print(f"Index created for {file_path}")
        return index

    def load_query_engine(self, participants, datasite_path, indexes=None):
        index_list = []
        index_summary = []
        for user_folder in participants:
            index_path: Path = Path(datasite_path) / \
                user_folder / "public" / "vector_index"
            if indexes is not None:
                index = indexes[user_folder]
            else:
                index = self.load_from_disk(persist_dir=index_path)
            index_list.append(index)
            index_summary.append(f"{user_folder}")

        graph = ComposableGraph.from_indices(
            VectorStoreIndex,
            index_list,
            index_summaries=index_summary
        )
        query_engine = graph.as_query_engine()
        return query_engine
