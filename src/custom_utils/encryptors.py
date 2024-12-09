import os
import json
import numpy as np
import tenseal as ts


def create_context():   # TenSEAL Context for key generation
    context = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus_degree=8192,
                         coeff_mod_bit_sizes=[60, 40, 40, 60])
    context.generate_galois_keys()
    context.global_scale = 2**40
    return context


def encrypt_embeddings(data, context):    # Encryption
    return ts.ckks_vector(context, data)


def encrypted_dot_product(query_vector, key_matrix):   # Function/Computation
    alignment_score = []
    for m in key_matrix:
        print(type(m), type(query_vector))
        encrypted_result = query_vector.dot(m)  # Perform the dot product
        decrypted_result = encrypted_result.decrypt()   # Decryption
        alignment_score.append(decrypted_result)
    return np.array(alignment_score)


def read_embeddings(input_file: str):
    with open(input_file, 'r') as file:
        data = json.load(file)
    return data


def encrypt_and_store_embeddings(input_folder: str,
                                 embedding_filename="default__vector_store.json",
                                 output_filename="encrypted__vector_store.json",
                                 context=None):
    if context is None:
        print("No context provided, making new")
        return
    embeddings = read_embeddings(input_folder / embedding_filename)["embedding_dict"]
    encrypted_embeddings = {}
    for key, value in embeddings.items():
        if isinstance(value, list):
            value = np.array(value, dtype=float)
        else:
            print(f"Skipping {key}: Value is not a valid list or array")
            continue
        encrypted_value = ts.ckks_vector(context, value)
        encrypted_embeddings[key] = encrypted_value.serialize().decode("utf-8")
    out_path = os.path.join(input_folder, output_filename)
    # print(type(encrypted_embeddings))
    with open(out_path, 'w', encoding='utf-8') as file:
        json.dump({"embedding_dict":encrypted_embeddings}, file)
    print(
        f"Encrypted embeddings have been saved to {out_path}")


def decrypt_embeddings(x):
    return x
