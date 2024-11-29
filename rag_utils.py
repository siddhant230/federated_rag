import os
import shutil
from pathlib import Path

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.llms.gemini import Gemini
from transformers import T5Tokenizer, T5ForConditionalGeneration

# custom imports
from custom_utils.custom_compose import GraphComposer

# TODO : Parth : Implement this file
from custom_utils.encryptors import encrypt_index

# llocal embedding model
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.embed_model = embed_model

# local llm-predictor
tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
llm = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")

# llm = Gemini(
#     model="models/gemini-1.5-flash",
#     # uses GOOGLE_API_KEY
#     api_key=open("config_key.txt").read(),
# )
Settings.llm = llm


def index_creator(file_path: str, target_path: str):
    doc = SimpleDirectoryReader(input_files=[file_path]).load_data()
    index = VectorStoreIndex.from_documents(doc)
    target_path = Path(target_path) / "vector_index"
    if os.path.exists(target_path):
        shutil.rmtree(target_path)

    index.storage_context.persist(persist_dir=target_path)
    print(f"Index created for {file_path}")
    encrypt_index(target_path)  # TODO
    print("Embeddings encrypted and saved!")
    return index


def load_query_engine(participants, datasite_path, indexes=None):
    index_path_list = []
    for user_folder in participants:
        index_path: Path = Path(datasite_path) / \
            user_folder / "public" / "vector_index"
        index_path_list.append(index_path)

    graph = GraphComposer(
        indexes_folder_paths=index_path_list,
        embedding_model=embed_model,
        llm=llm,
        tokenizer=tokenizer
    )
    return graph
