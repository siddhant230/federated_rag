from pathlib import Path
from syftbox.lib import Client, SyftPermission
import json
import os
from datetime import datetime

from src.lm_utils.embedding_models.base_embeds import BgeSmallEmbedModel
from src.lm_utils.llms.base_lm import T5LLM
from src.rag_utils import index_creator, load_query_engine

from src.data_utils.linkedin_extractor import LinkedinScraper
# TODO : similarly wrap git_scraper and import @vrinda


def should_run(output_file_path: str) -> bool:
    INTERVAL = 30
    if not os.path.exists(output_file_path):
        return True

    last_modified_time = datetime.fromtimestamp(
        os.path.getmtime(output_file_path))
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
    print("Computing indices")
    indexes = {}
    active_participants = []
    for user_folder in participants:
        value_file: Path = Path(datasite_path) / \
            user_folder / "public" / "bio.txt"
        if value_file.exists():
            index = index_creator(value_file, target_path=Path(
                datasite_path) / user_folder / "public")
            indexes[user_folder] = index
            active_participants.append(user_folder)
    print("Found {} indices and the active participants are: {}".format(
        len(indexes), active_participants))
    return active_participants


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


def perform_query(query, participants: list[str], datasite_path: Path,
                  embed_model, llm):
    midx_engine = load_query_engine(participants, datasite_path,
                                    embed_model=embed_model,
                                    llm=llm)
    print("Engine ready for querying..")
    response = midx_engine.generate(query)
    print("Query was executed succesfully.")
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
if __name__ == "__main__":

    # client and models loading
    client = Client.load()
    embed_model = BgeSmallEmbedModel()
    llm = T5LLM()

    # Setup folder paths
    output_folder = client.datasite_path / "api_data" / \
        "federated_rag" / "timestamp_recorder"
    input_query_folder = client.datasite_path / \
        "api_data" / "federated_rag" / "query_inbox"
    output_query_folder = client.datasite_path / \
        "api_data" / "federated_rag" / "query_outputs"

    for folder in [output_folder, input_query_folder, output_query_folder]:
        os.makedirs(folder, exist_ok=True)

    # Check if should run
    output_file_path = output_folder / "last_run.json"
    if not should_run(output_file_path):
        print("Skipping execution of federated_rag, not enough time has passed.")
        exit()
    save_run(output_folder, output_file_path)

    # Check which participants are active (have a public/bio.txt file)
    participants = network_participants(client.datasite_path.parent)

    # TODO : data scraping should be here @Vrinda
    # scrape_save_data(participants, client.datasite_path.parent)

    active_participants = make_index(participants, client.datasite_path.parent)

    # Use their public data to answer the question I added
    queries = load_queries(input_query_folder)
    for filename, query in queries.items():
        response = perform_query(query, active_participants,
                                 client.datasite_path.parent, embed_model=embed_model, llm=llm)
        print(response)
        output_response_path = output_query_folder / \
            "{}_{}.txt".format(filename.split('.')[0], datetime.now().date())

        with open(output_response_path, "w") as file:
            output = "Query: {}\nResponse: {}\n".format(query, response)
            file.write(output)

        # Remove query input
        input_path = input_query_folder / filename
        input_path.unlink(missing_ok=True)

# custom test
# if __name__ == "__main__":
#     datasite_path = "test_group_scientists"
#     participants = list(os.listdir(datasite_path))
#     make_index(participants, datasite_path)
#     resp = perform_query("summary about education of all of them?", participants, datasite_path)
#     print(resp)
