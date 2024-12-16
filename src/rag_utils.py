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
from src.custom_utils.encryptors import encrypt_and_store_embeddings, read_context


def index_creator(file_path: str, target_path: str, context):
    doc = SimpleDirectoryReader(input_files=[file_path]).load_data()
    index = VectorStoreIndex.from_documents(doc)
    target_path = Path(target_path) / "vector_index"
    if os.path.exists(target_path):
        shutil.rmtree(target_path)

    index.storage_context.persist(persist_dir=target_path)
    print(f"Index created for {file_path}")
    encrypt_and_store_embeddings(input_folder=target_path, context=context)
    print("Embeddings encrypted and saved!")
    return index


def load_query_engine(participants, datasite_path,
                      embed_model,
                      llm,
                      context,
                      indexes=None):
    index_path_list = []
    context_list = []
    for user_folder in participants:
        index_path: Path = Path(datasite_path) / \
            user_folder / "public" / "vector_index"
        context_path: Path = Path(datasite_path) / \
            user_folder / "public" / "secret_context.txt"

        context = read_context(context_path)
        index_path_list.append(index_path)
        context_list.append(context)

    graph = GraphComposer(
        indexes_folder_paths=index_path_list,
        embedding_model=embed_model,
        llm=llm,
        context=None,
        context_list=context_list
    )
    return graph
