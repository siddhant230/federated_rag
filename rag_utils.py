from llama_index.core.composability import ComposableGraph
from pathlib import Path
from llama_index.core import SimpleDirectoryReader
from llama_index.core import (
    VectorStoreIndex,
    SimpleKeywordTableIndex,
    SimpleDirectoryReader,
)
from llama_index.core import Settings

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM

# loads BAAI/bge-small-en # locally
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.embed_model = embed_model

# llm-predictor
# llm_predictor = LLMPredictor(model_name=LocalLLM())
# service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
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
    index.storage_context.persist(persist_dir=target_path)
    print("Index created")


def load_query_engine(participants, datasite_path):
    index_list = []
    for user_folder in participants:
        value_file: Path = Path(datasite_path) / \
            user_folder / "public"
        index = VectorStoreIndex.load_from_disk(persist_dir=value_file)
        index_list.append(index)

    graph = ComposableGraph.from_indices(
        SimpleKeywordTableIndex,
        index_list
    )
    query_engine = graph.as_query_engine()
    return query_engine
