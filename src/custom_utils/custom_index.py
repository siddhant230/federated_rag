import os
import json
import numpy as np


class CustomIndex:
    def __init__(self, base_index, storage_context,
                 base_index_folder,
                 # ideally this would be name of corresponding encrypted embeds
                 default_enc_filename="default__vector_store.json"
                 ):
        self.base_index = base_index
        self.base_index_folder = base_index_folder
        self.storage_context = storage_context

        self.vector_store = self.storage_context.vector_store
        self.docstore = self.storage_context.docstore
        self.default_enc_filename = default_enc_filename
        self.load_encrypted_embeddings()
        self.stack_info()

    def load_encrypted_embeddings(self):
        with open(os.path.join(self.base_index_folder, self.default_enc_filename)) as f:
            self.enc_embeds_store = json.load(f)["embedding_dict"]

    def stack_info(self):
        # makes enc and non-enc vectors matrix for each person folder
        self.encrypted_embedding_matrix = []
        self.unencrypted_embedding_matrix = []
        self.node_info = []
        self.text_info = []
        self.extra_info = []

        for node_id, embedding in self.base_index.vector_store.data.embedding_dict.items():
            node = self.base_index.docstore.get_node(node_id)
            encrypted_embedding = self.enc_embeds_store[node_id]

            self.encrypted_embedding_matrix.append(embedding)
            self.unencrypted_embedding_matrix.append(encrypted_embedding)
            self.node_info.append(node)
            self.text_info.append(node.text)
            self.extra_info.append(node.extra_info)
        self.encrypted_embedding_matrix = np.array(
            self.encrypted_embedding_matrix)
        self.unencrypted_embedding_matrix = np.array(
            self.unencrypted_embedding_matrix)
