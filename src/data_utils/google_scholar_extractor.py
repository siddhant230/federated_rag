import requests
from bs4 import BeautifulSoup


def google_scholar_extractor_util(profile_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.126 Safari/537.36"
    }
    extracted_info = {}
    response = requests.get(profile_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        extracted_info["name"] = soup.select_one("#gsc_prf_in").text
        extracted_info["affiliation"] = soup.select_one(".gsc_prf_il").text
        extracted_info["interests"] = ", ".join([
            interest.text for interest in soup.select(".gsc_prf_inta")])
        extracted_info["citations"] = int(soup.select(".gsc_rsb_std")[
            :2][0].text)
        extracted_info["h_index"] = int(soup.select(".gsc_rsb_std")[
            2:4][0].text)
        publications = soup.select(".gsc_a_t .gsc_a_at")
        publication_data = ""
        for pub in publications:
            publication_data += pub.text + "\n"
        extracted_info["publications"] = publication_data

    return extracted_info


# data = google_scholar_extractor(
#     "https://scholar.google.com/citations?user=JicYPdAAAAAJ&hl=en")
# print(data)
