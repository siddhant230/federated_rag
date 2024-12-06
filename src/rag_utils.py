import os
import shutil
from pathlib import Path

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader
)

# custom imports
from src.custom_utils.custom_compose import GraphComposer

# TODO : Parth : Implement this file
from src.custom_utils.encryptors import encrypt_and_store_embeddings


def index_creator(file_path: str, target_path: str):
    doc = SimpleDirectoryReader(input_files=[file_path]).load_data()
    index = VectorStoreIndex.from_documents(doc)
    target_path = Path(target_path) / "vector_index"
    if os.path.exists(target_path):
        shutil.rmtree(target_path)

    index.storage_context.persist(persist_dir=target_path)
    print(f"Index created for {file_path}")
    encrypt_and_store_embeddings(target_path)
    print("Embeddings encrypted and saved!")
    return index


def load_query_engine(participants, datasite_path,
                      embed_model,
                      llm, tokenizer,
                      indexes=None):
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
