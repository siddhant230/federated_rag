import requests
from bs4 import BeautifulSoup


def extract_portfolio_data(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for a in soup.find_all('a'):
            a.decompose()
        text = soup.get_text(separator="\n").strip().replace('\n\n', "")
        return text
    return f"No data found for {url}"


# url = "https://www.cmu.edu/epp/people/faculty/lorrie-faith-cranor.html"
# info = extract_portfolio_data(url)
# print(info)
