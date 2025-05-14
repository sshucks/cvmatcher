import re
from datetime import date
import json

# TODO Mabye define patterns in .txt or Json File

DATE_PATTERNS= [
    re.compile(r'^\s*(\d{4}-\d{2})\s*-\s*(JETZT|Jetzt|jetzt|heute)', re.IGNORECASE),  # ISO-Format mit "JETZT"
    re.compile(r'(?<!\d)\b(\d{4}\s*-\s*\d{4})\b'),
    re.compile(r'^\s*[\w\-.]?\s*(\d{4}\s*-\s*\d{4})'),  # Jahr zu Jahr
    re.compile(r'^\s*(\d{2}/\d{4})\s*–\s*(\d{2}/\d{4}|\s*)'),  # Monat/Jahr – Monat/Jahr
    re.compile(r'^\s*seit\s*(\d{2}/\d{4})\s*bis\s*(dato|JETZT|Jetzt|jetzt|heute)', re.IGNORECASE),  # seit MM/YYYY bis dato
    re.compile(r"^\s*(\b(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)\.?\s\d{4})\s*–\s*(\b(?:heute|JETZT|Jetzt|jetzt|(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Dez(?:ember)?)\.?\s\d{4})?)")
]


COMPANY_NAME_PATTERN = re.compile(
    #r'([A-Za-zäöüÄÖÜß]+(?:\s[A-Za-zäöüÄÖÜß]+)*)\s+(.+?)(?:\s/\s|$)'
    #r'([A-Za-zäöüÄÖÜß]+(?:\s[A-Za-zäöüÄÖÜß.,&()-]+)*)(?:\s+)?(?:[,|–|-]+\s*[^,]*)?$'
    r'([A-Za-zäöüÄÖÜß]+(?:\s[A-Za-zäöüÄÖÜß.,&-]+)*)(?=\s|$)'
)

JOB_TITLE_PATTERN= re.compile(
    r'^[A-Za-zäöüÄÖÜß]+(?:\s[A-Za-zäöüÄÖÜß.,-]+)*$' 
)

COMPANY_KEYWORDS = ["GmbH", "AG", "Inc.", "Co.", "Corp.", "LLC", "e.U.", "KG"]

def extract_work_experience(text: str) -> list[dict]:
    experience_points = text.splitlines()  
    structured_points = []
    point = None
    company_name = ""
    job_title = ""

    for i, line in enumerate(experience_points):
        date = None

        for date_pattern in DATE_PATTERNS:
            date_match = re.search(date_pattern, line)
            if date_match:
                date = date_match.group(0).strip()
                break  

        if date:
            if point:
                structured_points.append(point)

            company_name = ""
            if i + 1 < len(experience_points):
                next_line = experience_points[i + 1].strip()
                firm_match = re.search(COMPANY_NAME_PATTERN, next_line)
                if firm_match:
                    company_name = firm_match.group(0).strip()  

            description = line.replace(date, '').strip()  
            description = description.replace(company_name, "")
            

            point = {"date": date, "company_name": company_name, "description": description}

        else:
            if point:
                point["description"] += " " + line.strip()

    if point:
        structured_points.append(point)

    return structured_points

def save_to_json(data: str, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def extract_work(text_block: str, json_output_path: str = None) -> list[dict]:
    result = extract_work_experience(text_block)
    return result