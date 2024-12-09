import numpy as np

from llama_index.core import (
    Settings,
    StorageContext, load_index_from_storage
)

from custom_index import CustomIndex
# TODO : Parth : Implement this file
from encryptors import (encrypt_embeddings,
                        decrypt_embeddings,
                        encrypted_dot_product)


class GraphComposer:
    def __init__(self, indexes_folder_paths: list,
                 embedding_model,
                 llm, context):
        self.indexes_folder_paths = indexes_folder_paths
        # embedding mdoel has to be a HuggingFaceEmbedding class for Settings to function
        self.embedding_model = embedding_model
        # setting again might not be required, as Settings.embed_model works globally
        Settings.embed_model = embedding_model
        self.compose_indexes()
        # Setting.llm not required as we are not using llamaindex for inference/generation.
        self.llm = llm
        self.context = context

    def load_from_disk(self, persist_dir):
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        base_index = load_index_from_storage(storage_context)
        return base_index, storage_context

    def compose_indexes(self):
        indexes = []
        for index_folder in self.indexes_folder_paths:
            base_index, storage_context = self.load_from_disk(index_folder)
            custom_index = CustomIndex(
                base_index, storage_context, index_folder)
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
            self.global_encrypted_embedding_matrix.append(
                index.encrypted_embedding_matrix)
            self.global_unencrypted_embedding_matrix.append(
                index.unencrypted_embedding_matrix)
            self.global_node_info.append(index.node_info)
            self.global_text_info.append(index.text_info)
            self.global_extra_info.append(index.extra_info)

        self.global_unencrypted_embedding_matrix = np.array(
            self.global_unencrypted_embedding_matrix)
        self.global_encrypted_embedding_matrix = np.array(
            self.global_encrypted_embedding_matrix)

    def retriever(self, query, top_k=3):
        # get query embeds
        query_embedding = self.embedding_model.embed_data(query)
        # encrypt query embeds
        encrypted_query_embedding = encrypt_embeddings(
            query_embedding, context=self.context)

        # apply distance/sim metric
        similarity_scores = encrypted_dot_product(
            encrypted_query_embedding, self.global_encrypted_embedding_matrix)

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
            "encrypted_query_embedding": encrypted_query_embedding,
            "similarity_scores": similarity_scores,
            "top_k_indices": top_k_indices,
            "top_k_node_ids": top_k_node_ids
        }

    def generate(self, query, top_k=3):
        retrieved_out = self.retriever(query, top_k)
        collected_text_info = retrieved_out["collected_text_info"]
        context = "\n".join(collected_text_info)

        response = self.llm.generate_response(context, query)
        return response
