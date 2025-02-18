from collections import defaultdict
from pathlib import Path
from typing import List
from syftbox.lib import Client, SyftPermission
import json
import os
from datetime import datetime
import re

from src.custom_utils.encryptors import create_context
from src.lm_utils.embedding_models.base_embeds import BgeSmallEmbedModel
from src.lm_utils.llms.base_lm import T5LLM, GeminiLLM, OllamaLLM
from src.rag_utils import index_creator, load_query_engine

from src.data_utils.linkedin_extractor import LinkedinScraper
from src.data_utils.resume_extractor import pdf_to_text
from src.data_utils.github_extractor import get_github_user_info
from src.utils import remove_emails_and_phone_numbers

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter



def should_run(output_file_path: str) -> bool:
    INTERVAL = 120 # 2 minutes
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


def make_index(participants: list[str], datasite_path: Path, context, pipeline):
    print("Computing indices..")
    indexes = {}
    active_participants = []
    for user_folder in participants:
        value_file: Path = Path(datasite_path) / \
            user_folder / "public" / "bio.txt"
        if value_file.exists():
            index = index_creator(value_file, target_path=Path(
                datasite_path) / user_folder / "public", context=context, node_pipeline=pipeline)
            indexes[user_folder] = index
            active_participants.append(user_folder)
    print("Found {} indices and the active participants are: {}".format(
        len(indexes), active_participants))
    return active_participants


def network_participants(datasite_path: Path) -> List[str]:
    entries = os.listdir(datasite_path)
    return [entry for entry in entries if Path(datasite_path / entry).is_dir()]


def get_links_from_config(config_path: Path):
    links = {
        'linkedin': None,
        'github': None,
        'google_scholar': None,
        'twitter': None,
        'resume_path': None
    }

    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[^\s\'"<>]+'
    github_pattern = r'https?://(?:www\.)?github\.com/[^\s\'"<>]+'

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            content = json.load(file)
        user_links = content.get('links', {})
        if not isinstance(user_links, list):
            raise ValueError("'links' should be a list in the JSON file")

        for url in user_links:
            if re.match(linkedin_pattern, url, re.IGNORECASE):
                links['linkedin'] = url
            elif re.match(github_pattern, url, re.IGNORECASE):
                links['github'] = url

        links['resume_path'] = content.get('resume_path', None)
    except FileNotFoundError:
        pass
        print(f"Config file not found at {config_path}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return links


def scrape_save_data(participants: list[str], datasite_path: Path):
    active_participants = []
    inactive_participants = []
    sources_found = defaultdict(list)
    
    for participant in participants:
        participant_path = Path(datasite_path)/participant/"public"
        participant_path.mkdir(parents=True, exist_ok=True)
        bio_path = participant_path/"bio.txt"
        if bio_path.exists():
            print(
                f"Skipping data extraction for {participant}: bio already exists")
            continue
        config_path = participant_path / "config.json"
        links = get_links_from_config(config_path)
        extracted_info = []

        try:
            if links['linkedin']:
                try:
                    linkedin_scraper = LinkedinScraper(user_email='', pwd='')
                    profile_username = linkedin_scraper.get_profile_usr(
                        links['linkedin'])
                    profile_data = linkedin_scraper.scrape_profile(
                        profile_username)

                    extracted_info.append("# Linkedin Information:\n")
                    extracted_info.append(
                        remove_emails_and_phone_numbers(str(profile_data)))
                    
                    sources_found[participant].append('linkedin')
                except Exception as e:
                    print(f"LinkedIn scraping failed for {participant}: {e}")

            if links['github']:
                try:
                    git_data = get_github_user_info(links['github'])

                    extracted_info.append('# Github Information:\n')
                    extracted_info.append(
                        remove_emails_and_phone_numbers(git_data))
                    sources_found[participant].append('github')
                except Exception as e:
                    print(f"Github scraping failed for {participant}: {e}")

            if links['resume_path']:
                print(f"RESUME PATH: {links['resume_path']}")
                try:
                    resume_data = pdf_to_text(links['resume_path'])

                    extracted_info.append('# Resume: \n')
                    extracted_info.append(
                        remove_emails_and_phone_numbers(resume_data))
                    sources_found[participant].append('resume')

                except Exception as e:
                    print(f"Resume parsing failed for {participant}: {e}")

            if len(extracted_info) > 0:
                with open(bio_path, 'w', encoding='utf-8') as bio_file:
                    bio_file.writelines(extracted_info)
                    active_participants.append(participant)
                    # print(
                    #     f"Successfully processed and saved bio for {participant}")
            else:
                inactive_participants.append(participant)

        except Exception as e:
            print(f"Overall data extraction failed for {participant}: {e}")

    print(f"Contributing participants: {active_participants}")
    print(f"Non-contributing participants: {inactive_participants}")
    print(f'Sources found for each participant: {sources_found}')

def perform_query(query, participants: list[str], datasite_path: Path,
                  embed_model, llm, context):
    midx_engine = load_query_engine(participants, datasite_path,
                                    embed_model=embed_model,
                                    llm=llm, context=context)
    print("Engine ready for querying..")
    print("generating response!")
    response = midx_engine.generate(query, top_k=3)
    print("Query was executed succesfully.")
    return response


# syftbox relevant main
if __name__ == "__main__":

    # client and models loading
    client = Client.load()
    embed_model = BgeSmallEmbedModel()
    llm = OllamaLLM()  # T5LLM()

    pipeline = IngestionPipeline(
    transformations=[SentenceSplitter(
        chunk_size=50, chunk_overlap=10), embed_model.embedding_model])
    
    global_context = create_context()
    print(f"GLOBAL CONTEXT: {global_context}")

    # Setup folder paths
    output_folder = client.datasite_path / "api_data" / \
        "federated_rag" / "timestamp_recorder"

    os.makedirs(output_folder, exist_ok=True)

    # Check if should run
    output_file_path = output_folder / "last_run.json"
    if not should_run(output_file_path):
        print("Skipping execution of federated_rag, not enough time has passed.")
        exit()

    save_run(output_folder, output_file_path)

    # Check which participants are active (have a public/bio.txt file)
    participants = network_participants(client.datasite_path.parent)
    scrape_save_data(participants, client.datasite_path.parent)

    active_participants = make_index(
        participants, 
        client.datasite_path.parent,
        context=global_context, 
        pipeline=pipeline)
    