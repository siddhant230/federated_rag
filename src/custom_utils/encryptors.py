import os
import json
import base64
import numpy as np
import tenseal as ts


def create_context():   # TenSEAL Context for key generation
    context = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus_degree=8192,
                         coeff_mod_bit_sizes=[60, 40, 40, 60])
    context.generate_galois_keys()
    context.global_scale = 2**40
    return context


def read_context(filepath):
    with open(filepath, 'rb') as f:
        context = f.read()
    return base64.b64decode(context)


def write_context(context, filepath):
    if type(context) == bytes:
        context = base64.b64encode(context)

    with open(filepath, 'wb') as f:
        f.write(context)


def encrypt_embeddings(data, context):    # Encryption
    return ts.ckks_vector(context, data)


# Function/Computation
def encrypted_dot_product(query_vector, key_matrix, index_context_list):
    alignment_score = []
    for idx, m in enumerate(key_matrix):
        encrypted_query_embedding = encrypt_embeddings(
            query_vector, context=index_context_list[idx])
        encrypted_result = encrypted_query_embedding.dot(
            m)  # Perform the dot product
        decrypted_result = encrypted_result.decrypt()   # Decryption
        alignment_score.append(decrypted_result)
    return np.array(alignment_score)


def read_embeddings(input_file: str):
    with open(input_file, 'r') as file:
        data = json.load(file)
    return data


def read_encrypted_embeddings(file_path: str):
    with open(file_path, 'r') as f:
        loaded_data = json.load(f)

    encrypted_embeddings = loaded_data["embedding_dict"]

    for key, value in encrypted_embeddings.items():
        encrypted_embeddings[key] = base64.b64decode(value)

    return encrypted_embeddings


def encrypt_and_store_embeddings(input_folder: str,
                                 embedding_filename="default__vector_store.json",
                                 output_filename="encrypted__vector_store.json",
                                 context=None):
    if context is None:
        print("No context provided, making new")
        return
    embeddings = read_embeddings(
        input_folder / embedding_filename)["embedding_dict"]
    encrypted_embeddings = {}
    for key, value in embeddings.items():
        if isinstance(value, list):
            value = np.array(value, dtype=float)
        else:
            print(f"Skipping {key}: Value is not a valid list or array")
            continue
        encrypted_value = ts.ckks_vector(context, value)
        encrypted_embeddings[key] = encrypted_value.serialize()

    out_path = os.path.join(input_folder, output_filename)

    with open(out_path, 'w') as f:
        json.dump({"embedding_dict": str(encrypted_embeddings)}, f)

    print(f"Encrypted embeddings have been saved to {out_path}")

    # saving the contex for user
    context_path = os.path.join(input_folder, "secret_context.txt")
    write_context(context=context,
                  filepath=context_path)


def decrypt_embeddings(x):
    return x
