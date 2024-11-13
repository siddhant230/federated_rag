from pathlib import Path
from syftbox.lib import Client
import json
import os

from rag_utils import index_creator, load_query_engine


def make_index(participants: list[str], datasite_path: Path):
    for user_folder in participants:
        value_file: Path = Path(datasite_path) / \
            user_folder / "public" / "bio.txt"
        if "rsiddhant73" in value_file:
            print("########", value_file)
            if value_file.exists():
                index_creator(value_file, target_path=Path(
                    datasite_path) / user_folder / "public")


def perform_query(query, participants: list[str], datasite_path: Path):
    midx_engine = load_query_engine(participants, datasite_path)
    response = midx_engine.query(query)
    return response


def network_participants(datasite_path: Path):
    exclude_dir = ["apps", ".syft"]

    entries = os.listdir(datasite_path)

    users = []
    for entry in entries:
        if Path(datasite_path / entry).is_dir() and entry not in exclude_dir:
            users.append(entry)

    return users


if __name__ == "__main__":
    client = Client.load()

    participants = network_participants(client.datasite_path.parent)

    make_index(participants, client.datasite_path.parent)

    # question = input("Ask your query : ")
    question = "tell me about yourself?"
    perform_query(question)
    output_dir: Path = Path(client.datasite_path) / \
        "app_pipelines" / "basic_aggregation"
