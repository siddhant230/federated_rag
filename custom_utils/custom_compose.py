import numpy as np

from llama_index.core import (
    Settings,
    StorageContext, load_index_from_storage
)

from custom_index import CustomIndex
# TODO : Parth : Implement this file
from encryptors import encrypt_embeddings, decrypt_embeddings


class GraphComposer:
    def __init__(self, indexes_folder_paths: list,
                 embedding_model,
                 llm, tokenizer):
        self.indexes_folder_paths = indexes_folder_paths
        # embedding mdoel has to be a HuggingFaceEmbedding class for Settings to function
        self.embedding_model = embedding_model
        Settings.embed_model = embedding_model
        self.compose_indexes()

        self.llm = llm
        self.tokenizer = tokenizer

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
        query_embedding = self.embedding_model.get_query_embedding(query)
        # encrypt query embeds
        encrypted_query_embedding = encrypt_embeddings(query_embedding)

        # apply distance/sim metric
        similarity_scores = np.dot(self.global_unencrypted_embedding_matrix,
                                   encrypted_query_embedding).reshape(-1,)

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

    def make_prompt(self, context, query):
        return f"""
              Answer from given context, Be very specific and accurate.
              {context}
              Question: {query}
              Answer:
            """

    def generate(self, query, top_k=3):
        retrieved_out = self.retriever(query, top_k)
        collected_text_info = retrieved_out["collected_text_info"]
        concatenated_info = "\n".join(collected_text_info)

        # this could be anything
        prompt = self.make_prompt(concatenated_info, query)
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids
        outputs = self.llm.generate(input_ids, max_new_tokens=256)
        out = self.tokenizer.decode(outputs[0]).replace(concatenated_info, "")

        return out
