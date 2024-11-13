from pathlib import Path

from llama_index.core import (
    VectorStoreIndex,
    SimpleKeywordTableIndex,
    SimpleDirectoryReader,
    Settings
)
from llama_index.core.composability import ComposableGraph
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM

# llocal embedding model
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.embed_model = embed_model

# local llm-predictor
llm_predictor = HuggingFaceLLM(
    model_name="distilbert/distilgpt2",
    tokenizer_name="distilbert/distilgpt2",
    context_window=3900,
    max_new_tokens=256,
    device_map="auto",
)
Settings.llm = llm_predictor


def index_creator(file_path: str, target_path: str):
    doc = SimpleDirectoryReader(input_files=[file_path]).load_data()
    index = VectorStoreIndex.from_documents(doc)
    target_path = Path(target_path) / "vector_index"
    index.storage_context.persist(persist_dir=target_path)
    print("Index created")


def load_query_engine(participants, datasite_path):
    index_list = []
    for user_folder in participants:
        index_path: Path = Path(datasite_path) / \
            user_folder / "public" / "vector_index"
        index = VectorStoreIndex.load_from_disk(persist_dir=index_path)
        index_list.append(index)

    graph = ComposableGraph.from_indices(
        SimpleKeywordTableIndex,
        index_list
    )
    query_engine = graph.as_query_engine()
    return query_engine
