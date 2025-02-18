import numpy as np

from llama_index.core import (
    Settings,
    StorageContext, load_index_from_storage
)

from src.custom_utils.custom_index import CustomIndex
# TODO : Parth : Implement this file
from src.custom_utils.encryptors import (encrypt_embeddings,
                                         decrypt_embeddings,
                                         encrypted_dot_product)


import json
import os


class GraphComposer:
    def __init__(self, indexes_folder_paths: list,
                 embedding_model,
                 llm, context):
        self.indexes_folder_paths = indexes_folder_paths
        # embedding mdoel has to be a HuggingFaceEmbedding class for Settings to function
        self.embedding_model = embedding_model
        self.llm = llm
        self.context = context
        # setting again might not be required, as Settings.embed_model works globally
        Settings.embed_model = embedding_model.embedding_model
        self.compose_indexes()
        # Setting.llm not required as we are not using llamaindex for inference/generation.

    def load_from_disk(self, persist_dir):
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        base_index = load_index_from_storage(storage_context)
        return base_index, storage_context

    def compose_indexes(self):
        indexes = []
        for index_folder in self.indexes_folder_paths:
            base_index, storage_context = self.load_from_disk(index_folder)
            custom_index = CustomIndex(
                base_index, storage_context, index_folder,
                encryption_context=self.context)
            indexes.append(custom_index)

        self.stack_info(indexes)

    def stack_info(self, indexes):
        # makes enc and non-enc vectors matrix for across all persons folder
        self.global_encrypted_embedding_matrix = []
        self.global_unencrypted_embedding_matrix = []
        self.global_node_info = []
        self.global_text_info = []
        self.global_extra_info = []

        for index in indexes:
            self.global_encrypted_embedding_matrix.extend(
                index.encrypted_embedding_matrix)
            self.global_unencrypted_embedding_matrix.extend(
                index.unencrypted_embedding_matrix)
            self.global_node_info.extend(index.node_info)
            self.global_text_info.extend(index.text_info)
            self.global_extra_info.extend(index.extra_info)

        self.global_unencrypted_embedding_matrix = np.array(
            self.global_unencrypted_embedding_matrix)
        self.global_encrypted_embedding_matrix = np.array(
            self.global_encrypted_embedding_matrix)

    def write_stats(self, fname):
        current_pageviews = {"views": 1}
        if os.path.exists(fname):
            print("Page views are loaded and updated")
            in_file = open(fname, "r")
            in_file = in_file.read().strip()
            if in_file:
                current_pageviews = json.load(open(fname, "r"))
                current_pageviews['views'] += 1
        with open(fname, "w") as f:
            json.dump(current_pageviews, f)
        print("Page views have been written successfully")

    def enc_retriever(self, query, top_k=3):
        # get query embeds
        top_k = min(top_k, len(self.global_encrypted_embedding_matrix))
        query_embedding = self.embedding_model.embed_data(query)
        # encrypt query embeds
        encrypted_query_embedding = encrypt_embeddings(
            query_embedding, context=self.context)

        # apply distance/sim metric
        similarity_scores = encrypted_dot_product(
            encrypted_query_embedding, self.global_encrypted_embedding_matrix).reshape(-1,)
        # select top_k
        top_k_indices = np.argpartition(similarity_scores, -top_k)[-top_k:]

        # collect text-info
        collected_text_info = []
        top_k_node_ids = []

        # Current topK metadata
        top_k_metadata = []
        for i in top_k_indices:
            identifier = self.global_node_info[i].metadata['file_path'].split(os.sep+"public")[
                0].split(os.sep)[-1]
            identifier = "Name of the person :" + identifier + "\n"
            text_blob = identifier + "Info of the person:\n" + \
                self.global_text_info[i].replace("\n\n\n", "")
            collected_text_info.append(text_blob)
            top_k_node_ids.append(self.global_node_info[i])

            # Fetch the current meta data from the meta data inside the filapath
            current_metadata = self.global_node_info[i].metadata['file_path']
            top_k_metadata.append(current_metadata)

        # Set of topK files (unique per user)
        top_k_metadata = list(set(top_k_metadata))
        for metadata in top_k_metadata:
            stats_fpath = metadata.split("bio.txt")[0]
            stats_fpath = os.path.join(stats_fpath, "pageviews.json")
            self.write_stats(stats_fpath)

        return {
            "query": query,
            "collected_text_info": collected_text_info,
            "query_embedding": query_embedding,
            "encrypted_query_embedding": encrypted_query_embedding,
            "similarity_scores": similarity_scores,
            "top_k_indices": top_k_indices,
            "top_k_node_ids": top_k_node_ids
        }

    def retriever(self, query, top_k=3):
        # get query embeds
        top_k = min(top_k, self.global_unencrypted_embedding_matrix.shape[1])

        query_embedding = self.embedding_model.embed_data(query)

        similarity_scores = np.dot(self.global_unencrypted_embedding_matrix,
                                   query_embedding).reshape(-1,)
        # select top_k
        top_k_indices = np.argpartition(similarity_scores, -top_k)[-top_k:]

        # collect text-info
        collected_text_info = []
        top_k_node_ids = []
        for i in top_k_indices:
            identifier = self.global_node_info[i].metadata['file_path'].split(os.sep+"public")[
                0].split(os.sep)[-1]
            identifier = "This text belong to :" + identifier + "\n"
            text_blob = identifier + "Info of the person:\n" + \
                self.global_text_info[i].replace("\n\n\n", "")
            collected_text_info.append(text_blob)
            top_k_node_ids.append(self.global_node_info[i])

        return {
            "query": query,
            "collected_text_info": collected_text_info,
            "query_embedding": query_embedding,
            "encrypted_query_embedding": query_embedding,
            "similarity_scores": similarity_scores,
            "top_k_indices": top_k_indices,
            "top_k_node_ids": top_k_node_ids
        }

    def generate(self, query, top_k=3, sep="---------"):
        retrieved_out = self.enc_retriever(query, top_k)
        collected_text_info = retrieved_out["collected_text_info"]
        context = f"\n{sep}\n".join(collected_text_info)
        response = self.llm.generate_response(context, query)
        return response
