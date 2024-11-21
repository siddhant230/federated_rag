import os
from pathlib import Path
from syftbox.lib import Client

from rag_utils import RagUtilities


class FedRagEngine:
    def __init__(self, participants, datasite_path):
        self.rag_utils = RagUtilities()
        print("Preparing indexes")
        self.make_index(participants, datasite_path)
        self.midx_engine = self.rag_utils.load_query_engine(
            participants, datasite_path)
        print("Engine ready")

    def make_index(self, participants: list[str], datasite_path: Path):
        indexes = {}
        for user_folder in participants:
            value_file: Path = Path(datasite_path) / \
                user_folder / "public" / "bio.txt"
            if value_file.exists():
                index = self.rag_utils.index_creator(value_file, target_path=Path(
                    datasite_path) / user_folder / "public")
            indexes[user_folder] = index
        return indexes

    def perform_query(self, query):
        response = self.midx_engine.query(query)
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
    fed_engine_obj = FedRagEngine(
        participants, datasite_path=client.datasite_path.parent)

    # question = input("Ask your query : ")
    question = "tell me about their education?"
    response = fed_engine_obj.perform_query(question)
    output_dir: Path = Path(client.datasite_path) / \
        "app_pipelines" / "basic_aggregation"


# custom test
# if __name__ == "__main__":
#     datasite_path = "test_group_scientists"
#     participants = list(os.listdir(datasite_path))

#     fed_engine_obj = FedRagEngine(
#         participants, datasite_path=datasite_path)

#     # question = input("Ask your query : ")
#     question = "tell me about their education?"
#     response = fed_engine_obj.perform_query(question)
#     print(response)
