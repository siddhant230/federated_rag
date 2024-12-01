#!/usr/bin/env python
# coding: utf-8

# In[1]:


#pip install tenseal


# Function 1

# In[10]:


import tenseal as ts
import json
import numpy as np
from pathlib import Path
def create_context():   # TenSEAL Context for key generation
    context = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus_degree=8192, coeff_mod_bit_sizes=[60, 40, 40, 60])
    context.generate_galois_keys()
    context.global_scale = 2**40
    return context

def encrypt_data(data, context):    # Encryption
    return ts.ckks_vector(context, data)

def encrypted_dot_product(vector1, vector2, context):   # Function/Computation
    encrypted_vector1 = encrypt_data(vector1, context)
    encrypted_vector2 = encrypt_data(vector2, context)                                                            
    encrypted_result = encrypted_vector1.dot(encrypted_vector2) # Perform the dot product
    
    decrypted_result = encrypted_result.decrypt()   # Decryption
    
    return decrypted_result

if __name__ == "__main__":
    vector1 = [1, 2, 3, 4]  #example case
    vector2 = [5, 6, 7, 8]
    
    context = create_context()  # Create context
    
    result = encrypted_dot_product(vector1, vector2, context)       # Encrypted Computation
    
    print(f"The dot product of the two vectors is: {result}")


# Function 2

# In[11]:

def read_embeddings(input_file: str):
    with open(input_file, 'r') as file:
        data = json.load(file)
    return data

# Function to encrypt the embeddings and store in a new JSON file
def encrypt_and_store_embeddings(input_file: str, output_file: str):
    context = create_context()
    embeddings = read_embeddings(input_file)

    encrypted_embeddings = {}   
    for key, value in embeddings.items():
        # Ensure value is a list or numpy array of floats
        if isinstance(value, list):
            # If it's a list, convert to numpy array for compatibility
            value = np.array(value, dtype=float)
        else:
            print(f"Skipping {key}: Value is not a valid list or array")
            continue

        # Encrypt the value using CKKS
        encrypted_value = ts.ckks_vector(context, value)
        encrypted_embeddings[key] = encrypted_value.serialize()  # Serialize the encrypted vector

    # Write the encrypted embeddings to the output JSON file
    with open(output_file, 'w') as file:
        json.dump(encrypted_embeddings, file)

    print(f"Encrypted embeddings have been saved to {output_file}")

# Example usage:
if __name__ == "__main__":
    input_path = 'test_group_scientists/a/public/vector_index/default__vector_store.json'  # Path to input vector store
    output_path = 'test_group_scientists/a/public/vector_index/encrypted_vector_store.json'  # Path for storing encrypted embeddings
    encrypt_and_store_embeddings(input_path, output_path)


# Function 3

# In[8]:

def decrypt_and_store_embeddings(input_file: str, output_file: str, context):
    """
    Function to decrypt embeddings stored in a JSON file and save them to a new JSON file.
    """
    # Read the encrypted embeddings from the input file
    with open(input_file, 'r') as file:
        encrypted_embeddings = json.load(file)

    decrypted_embeddings = {}

    # Decrypt each embedding
    for key, encrypted_value in encrypted_embeddings.items():
        # Deserialize the encrypted vector
        encrypted_vector = ts.ckks_vector_from(serialized=encrypted_value, context=context)
        decrypted_value = encrypted_vector.decrypt()  # Decrypt the vector

        # Convert the decrypted value to a list and store it
        decrypted_embeddings[key] = decrypted_value.tolist()

    # Write the decrypted embeddings to the output JSON file
    with open(output_file, 'w') as file:
        json.dump(decrypted_embeddings, file)

    print(f"Decrypted embeddings have been saved to {output_file}")

# Example usage:
if __name__ == "__main__":
    input_path = 'test_group_scientists/a/public/vector_index/encrypted_vector_store.json'  # Path to input encrypted embeddings
    output_path = 'test_group_scientists/a/public/vector_index/decrypted_vector_store.json'  # Path for storing decrypted embeddings

    # Create context using the same parameters as used for encryption
    context = create_context()

    decrypt_and_store_embeddings(input_path, output_path, context)

