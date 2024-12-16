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


class GraphComposer:
    def __init__(self, indexes_folder_paths: list,
                 embedding_model,
                 llm, context, context_list):
        self.indexes_folder_paths = indexes_folder_paths
        # embedding mdoel has to be a HuggingFaceEmbedding class for Settings to function
        self.embedding_model = embedding_model
        self.llm = llm
        self.context = context  # would be None in case of non-global/user-level key
        self.context_list = context_list
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
        for index_folder, context in zip(self.indexes_folder_paths, self.context_list):
            base_index, storage_context = self.load_from_disk(index_folder)
            custom_index = CustomIndex(
                base_index, storage_context, index_folder,
                encryption_context=context)
            indexes.append(custom_index)

        self.stack_info(indexes)

    def stack_info(self, indexes):
        # makes enc and non-enc vectors matrix for across all persons folder
        self.global_encrypted_embedding_matrix = []
        self.global_unencrypted_embedding_matrix = []
        self.global_node_info = []
        self.global_text_info = []
        self.global_extra_info = []
        self.global_context_list = []

        for index in indexes:
            self.global_encrypted_embedding_matrix.extend(
                index.encrypted_embedding_matrix)
            self.global_unencrypted_embedding_matrix.extend(
                index.unencrypted_embedding_matrix)
            self.global_node_info.extend(index.node_info)
            self.global_text_info.extend(index.text_info)
            self.global_extra_info.extend(index.extra_info)
            self.global_context_list.extend(index.index_context_list)

        self.global_unencrypted_embedding_matrix = np.array(
            self.global_unencrypted_embedding_matrix)
        self.global_encrypted_embedding_matrix = np.array(
            self.global_encrypted_embedding_matrix)

    def enc_retriever(self, query, top_k=3):
        # get query embeds
        top_k = min(top_k, len(self.global_encrypted_embedding_matrix))
        query_embedding = self.embedding_model.embed_data(query)

        # apply distance/sim metric
        similarity_scores = encrypted_dot_product(
            query_embedding, self.global_encrypted_embedding_matrix,
            self.global_context_list).reshape(-1,)
        # select top_k
        top_k_indices = np.argpartition(similarity_scores, -top_k)[-top_k:]

        # collect text-info
        collected_text_info = []
        top_k_node_ids = []
        for i in top_k_indices:
            collected_text_info.append(self.global_text_info[i])
            top_k_node_ids.append(self.global_node_info[i])

        return {
            "query": query,
            "collected_text_info": collected_text_info,
            "query_embedding": query_embedding,
            "encrypted_query_embedding": None,
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
            collected_text_info.append(self.global_text_info[i])
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

    def generate(self, query, top_k=3):
        retrieved_out = self.enc_retriever(query, top_k)
        collected_text_info = retrieved_out["collected_text_info"]
        context = "\n".join(collected_text_info)

        response = self.llm.generate_response(context, query)
        return response
