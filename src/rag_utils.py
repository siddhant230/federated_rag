import os
import shutil
from pathlib import Path

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
)

# custom imports
from src.custom_utils.custom_compose import GraphComposer

# TODO : Parth : Implement this file
from src.custom_utils.encryptors import encrypt_and_store_embeddings


def index_creator(file_path: str, target_path: str, context, node_pipeline):
    # if os.path.exists(Path(target_path) / "vector_index"):
    #     return []
    doc = SimpleDirectoryReader(input_files=[file_path]).load_data()
    # run the pipeline
    nodes = node_pipeline.run(documents=doc)
    index = VectorStoreIndex(nodes)

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
    for user_folder in participants:
        index_path: Path = Path(datasite_path) / \
            user_folder / "public" / "vector_index"
        index_path_list.append(index_path)

    graph = GraphComposer(
        indexes_folder_paths=index_path_list,
        embedding_model=embed_model,
        llm=llm,
        context=context
    )
    return graph
