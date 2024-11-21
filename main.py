from pathlib import Path
from syftbox.lib import Client
import json
import os

from rag_utils import index_creator, load_query_engine


def make_index(participants: list[str], datasite_path: Path):
    indexes = {}
    for user_folder in participants:
        value_file: Path = Path(datasite_path) / \
            user_folder / "public" / "bio.txt"
        if value_file.exists():
            index = index_creator(value_file, target_path=Path(
                datasite_path) / user_folder / "public")
        indexes[user_folder] = index
    return indexes


def perform_query(query, participants: list[str], datasite_path: Path):
    midx_engine = load_query_engine(participants, datasite_path)
    print("Engine ready")
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
if __name__ == "__main__":
    client = Client.load()

    participants = network_participants(client.datasite_path.parent)

    make_index(participants, client.datasite_path.parent)

    # question = input("Ask your query : ")
    question = "tell me about their education?"
    response = perform_query(question, participants,
                             client.datasite_path.parent)
    output_dir: Path = Path(client.datasite_path) / \
        "app_pipelines" / "basic_aggregation"


# custom test
# if __name__ == "__main__":
#     datasite_path = "test_group_scientists"
#     participants = list(os.listdir(datasite_path))
#     make_index(participants, datasite_path)
#     resp = perform_query("summary about education of all of them?", participants, datasite_path)
#     print(resp)
