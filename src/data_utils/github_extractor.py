import os
import requests
import json
import markdown
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
# add github token for increased rate limit
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def md_to_text(md: str) -> str:
    """
    convert markdown into html rendered text
    """
    html = markdown.markdown(md)
    soup = BeautifulSoup(html, features='html.parser')
    return soup.get_text()


def get_github_user_info(profile_url, word_limit=100):
    """
    given a github profile URL, fetch user details + user readme and save to '../github_data/username.txt'
    """
    username = profile_url.rstrip('/').split('/')[-1]

    user_api_url = f"https://api.github.com/users/{username}"
    repos_api_url = f"https://api.github.com/users/{username}/repos"

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    user_response = requests.get(user_api_url, headers=headers)
    if user_response.status_code != 200:
        print(
            f"Error fetching user info: {user_response.json().get('message', 'Unknown error')}")
        return

    user_info = user_response.json()

    # pagination logic
    all_repos = []
    page = 1
    while True:
        response = requests.get(repos_api_url, headers=headers, params={
                                "page": page, "per_page": 100})
        if user_response.status_code != 200:
            print(
                f"Error fetching user info: {user_response.json().get('message', 'Unknown error')}")
            return
        repos = response.json()
        if not repos:
            break

        all_repos.extend(repos)
        page += 1

    readme_response = None

    # check for usr readme in main/master branches of all repos
    available_repos_data = []
    person_info = []
    for repo in all_repos:

        branches = ['main', 'master']
        readme_found = False
        for branch in branches:
            readme_url = f"https://raw.githubusercontent.com/{username}/{repo['name']}/{branch}/README.md"
            readme_response = requests.get(readme_url)
            if readme_response.status_code != 200:
                continue

            if repo.get('name').lower() == username.lower():
                person_info.append(readme_response.text)
            else:
                readme_response = " ".join(
                    readme_response.text.split(" ")[:word_limit])
                readme_response = f"Repo name:{repo}\nRepo description{readme_response}"
                available_repos_data.append(readme_response)

    if readme_response is not None:
        person_info = md_to_text("\n".join(person_info))
        available_repos_data = md_to_text("\n".join(available_repos_data))
        return "Information about person : " + person_info + "\n" + "His projects" + available_repos_data

    return f"No github data found for {profile_url}"

    # os.makedirs('./github_data', exist_ok=True)

    # with open(f'./github_data/{username}.txt', 'w') as f:
    #     json.dump(user_info, f)
    #     f.write('\n-------------------------\n')
    #     if readme_response and readme_response.status_code == 200:
    #         f.write(md_to_text(readme_response.text))
    #     f.close()


# if __name__ == "__main__":
#     url = "https://github.com/siddhant230"
#     data = get_github_user_info(profile_url=url)
#     print(data)
