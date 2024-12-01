from pathlib import Path
from syftbox.lib import Client, SyftPermission
import json
import os
from datetime import datetime

from rag_utils import index_creator, load_query_engine
from experiments.FHE_functions import create_context, encrypt_and_store_embeddings, decrypt_and_store_embeddings


def should_run(output_file_path: str) -> bool:
    INTERVAL = 30
    if not os.path.exists(output_file_path):
        return True

    last_modified_time = datetime.fromtimestamp(os.path.getmtime(output_file_path))
    time_diff = datetime.now() - last_modified_time

    if time_diff.total_seconds() >= INTERVAL:
        return True
    return False

def save_run(output_folder: str, output_file_path: str):
    os.makedirs(output_folder, exist_ok=True)
    timestamp_data = {"last_run": datetime.now().isoformat()}
    
    # Write timestamp to output file
    with open(output_file_path, "w") as f:
        json.dump(timestamp_data, f, indent=2)

    # Ensure permission file exists
    permission = SyftPermission.mine_with_public_read(email=client.email)
    permission.ensure(output_folder)
    print(f"Timestamp has been written to {output_file_path}")

def make_index(participants: list[str], datasite_path: Path):
    print("Encrypting and computing indices")

    # Create encryption context
    context = create_context()
    
    for user_folder in participants:
        vector_store_file = Path(datasite_path) / user_folder / "public" / "vector_index" / "default__vector_store.json"
        encrypted_file = Path(datasite_path) / user_folder / "public" / "vector_index" / "encrypted_vector_store.json"
        
        if vector_store_file.exists():
            # Encrypt embeddings
            encrypt_and_store_embeddings(str(vector_store_file), str(encrypted_file))
            
            print(f"Encrypted vector store for {user_folder} and saved to {encrypted_file}")
        else:
            print(f"Vector store not found for {user_folder}")


def load_queries(input_query_folder: str):
    queries = {}

    files = os.listdir(input_query_folder)
    for filename in files:
        file_path = os.path.join(input_query_folder, filename)
        
        if os.path.isdir(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            queries[filename] = content

    return queries
        

def perform_query(query, participants: list[str], datasite_path: Path):
    # Create context for decryption
    context = create_context()

    for user_folder in participants:
        encrypted_file = Path(datasite_path) / user_folder / "public" / "vector_index" / "encrypted_vector_store.json"
        decrypted_file = Path(datasite_path) / user_folder / "public" / "vector_index" / "decrypted_vector_store.json"

        if encrypted_file.exists():
            # Decrypt embeddings for querying
            decrypt_and_store_embeddings(str(encrypted_file), str(decrypted_file), context)
            print(f"Decrypted embeddings for {user_folder} and saved to {decrypted_file}")
        else:
            print(f"Encrypted vector store not found for {user_folder}")

    # Proceed with querying as usual
    midx_engine = load_query_engine(participants, datasite_path)
    response = midx_engine.query(query)
    return response.response


def network_participants(datasite_path: Path):
    exclude_dir = ["apps", ".syft"]

    entries = os.listdir(datasite_path)

    users = []
    for entry in entries:
        if Path(datasite_path / entry).is_dir() and entry not in exclude_dir:
            users.append(entry)

    return users


# syftbox relevant main
#if __name__ == "__main__":

#    client = Client.load()

    # Setup folder paths
#    output_folder = client.datasite_path / "api_data" / "federated_rag" / "timestamp_recorder"
##    input_query_folder = client.datasite_path / "api_data" / "federated_rag" / "query_inbox"
#    output_query_folder = client.datasite_path / "api_data" / "federated_rag" / "query_outputs"
    
#    for folder in [output_folder, input_query_folder, output_query_folder]:
#        os.makedirs(folder, exist_ok=True)
    
    # Check if should run
##    output_file_path = output_folder / "last_run.json"
#    if not should_run(output_file_path):
#        print("Skipping execution of federated_rag, not enough time has passed.")
#        exit()
#    save_run(output_folder, output_file_path)

    # Check which participants are active (have a public/bio.txt file)
#    participants = network_participants(client.datasite_path.parent)
#    active_participants = make_index(participants, client.datasite_path.parent)

    # Use their public data to answer the question I added
#    queries = load_queries(input_query_folder)
#    for filename, query in queries.items():
#        response = perform_query(query, active_participants,
#                                client.datasite_path.parent)
#        print(response)
#        output_response_path = output_query_folder / "{}_{}.txt".format(filename.split('.')[0], datetime.now().date())

#        with open(output_response_path, "w") as file:
#            output = "Query: {}\nResponse: {}\n".format(query, response)
#            file.write(output)

        # Remove query input
##        input_path = input_query_folder / filename
#        input_path.unlink(missing_ok=True)

# custom test
if __name__ == "__main__":
    datasite_path = "test_group_scientists"
    participants = list(os.listdir(datasite_path))
    make_index(participants, datasite_path)
    resp = perform_query("summary about education of all of them?", participants, datasite_path)
    print(resp)
