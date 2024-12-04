import linkedin_api
from dataclasses import dataclass, field
import re
import json
import os


@dataclass
class LinkedinScraper:
    user_email: str = field(default=None)
    pwd: str = field(default=None)

    def get_profile_usr(self, profile_url):
        pattern = r"linkedin\.com/(?:[a-z]{2,3}/)?(?:in|[\w-]+)/([^/]+)/?"
        match = re.search(pattern, profile_url)
        return match.group(1) if match else None

    def scrape_profile(self, profile_user):
        print(profile_user)
        api = linkedin_api.Linkedin(
            username=self.user_email, password=self.pwd)
        return api.get_profile(profile_user)

    def clean_profile_data(self, data):
        clean_data = {
            "Name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
            "Location": data.get("locationName", ""),
            "Current Position": data.get("headline", ""),
            "Summary": data.get("summary", ""),
            "Experience": [],
            "Education": [],
            "Certifications": [],
            "Skills": [skill.get("name", "") for skill in data.get("skills", [])],
            "Industry": data.get("industryName", "")
        }
        for exp in data.get("experience", []):
            clean_data["Experience"].append({
                "Company Name": exp.get("companyName", ""),
                "Role": exp.get("title", ""),
                "Location": exp.get("locationName", ""),
                "Start Date": exp.get("timePeriod", {}).get("startDate", {}),
                "End Date": exp.get("timePeriod", {}).get("endDate", {}),
                "Description": exp.get("description", ""),
                "Industries": exp.get("industries", [])
            })
        for edu in data.get("education", []):
            clean_data["Education"].append({
                "Institution": edu.get("schoolName", ""),
                "Degree": edu.get("degreeName", ""),
                "Field of Study": edu.get("fieldOfStudy", ""),
                "Grade": edu.get("grade", "")
            })

        for cert in data.get("certifications", []):
            clean_data["Certifications"].append({
                "Name": cert.get("name", ""),
                "Authority": cert.get("authority", ""),
                "License Number": cert.get("licenseNumber", ""),
                "URL": cert.get("url", "")
            })

        return clean_data

    def save_profile_data(self, profile_url: str, output_dir: str = './linkedin-data'):
        os.makedirs(output_dir, exist_ok=True)
        profile_username = self.get_profile_usr(profile_url)
        profile_data = self.scrape_profile(profile_username)
        try:
            with open(f"{output_dir}/{profile_username}", 'w', encoding='utf-8') as file:
                json.dump(self.clean_profile_data(
                    profile_data), file, ensure_ascii=False)
        except Exception as e:
            print("error while saving", e)
