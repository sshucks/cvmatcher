import re
import json
import dateparser
from datetime import date
from collections import defaultdict
#from docx2python import docx2python
import fitz

# TODO Mabye define patterns in .txt or Json File

DATE_PATTERNS = [
    re.compile(r'\b(\d{4})\s*-\s*(HEUTE|Jetzt|jetzt|heute)\b', re.IGNORECASE),  # Jahr mit "HEUTE"
    re.compile(r'^\s*\b\d{4}\b\s*[--]\s*(heute|JETZT|Jetzt|jetzt)', re.IGNORECASE),  # Jahr bis heute (z.B., "2008 - heute" ohne "bis")
    re.compile(r'\b\d{4}\b\s*[--]\s*(bis\s*)?(heute|JETZT|Jetzt|jetzt)', re.IGNORECASE),  # Jahr bis heute mit "bis" (z.B., "2008 - bis heute")
    re.compile(r'\b\d{4}\s*[--]\s*\b\d{4}\b'),  # Jahr zu Jahr (YYYY - YYYY)
    re.compile(r'^\s*[\w\-.]?\s*(\d{4}\s*[--]\s*\d{4})'),  # Jahr zu Jahr mit optionalem Präfix
    re.compile(r'\b\d{2}/\d{4}\s*[--]\s*\d{2}/\d{4}|\b\d{2}/\d{4}\s*[-–]\s*(heute|JETZT|Jetzt|jetzt)', re.IGNORECASE),  # Monat/Jahr bis Monat/Jahr oder heute
    re.compile(r'^\s*seit\s*(\d{2}/\d{4})\s*bis\s*(dato|JETZT|Jetzt|jetzt|heute)', re.IGNORECASE),  # seit MM/YYYY bis dato
    re.compile(r"^\s*(\b(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|Jul(?:i)?|Aug(?:ust)?|Sep(?:tember)?|Okt(?:ober)|Nov(?:ember)|Dez(?:ember)?)\.?\s\d{4})\s*[-–]\s*(\b(?:heute|JETZT|Jetzt|jetzt|(?:Jan(?:uar)?|Feb(?:ruar)|Mär(?:z)|Apr(?:il)|Mai|Jun(?:i)|Jul(?:i)|Aug(?:ust)|Sep(?:tember)|Okt(?:ober)|Nov(?:ember)|Dez(?:ember)?)\.?\s\d{4})?)", re.IGNORECASE)  # Monat ausgeschrieben mit Jahr
]


COMPANY_NAME_PATTERN = re.compile(
    #r'([A-Za-zäöüÄÖÜß]+(?:\s[A-Za-zäöüÄÖÜß]+)*)\s+(.+?)(?:\s/\s|$)'
    #r'([A-Za-zäöüÄÖÜß]+(?:\s[A-Za-zäöüÄÖÜß.,&()-]+)*)(?:\s+)?(?:[,|–|-]+\s*[^,]*)?$'
    r'([A-Za-zäöüÄÖÜß]+(?:\s[A-Za-zäöüÄÖÜß.,&-]+)*)(?=\s|$)'
)

JOB_TITLE_PATTERN = re.compile(
    r'^[A-Za-zäöüÄÖÜß]+(?:\s[A-Za-zäöüÄÖÜß.,-]+)*$' 
)

# COMPANY_KEYWORDS = ["GmbH", "AG", "Inc.", "Co.", "Corp.", "LLC", "e.U.", "KG"]


def check_date_position(line, normalize = True):
    date_found = False
    date_position = 'none'
    date_text = ""

    for pattern in DATE_PATTERNS:
        date_match = pattern.search(line)
        if date_match:
            date_text = date_match.group(0).strip()
            date_found = True
            
            if normalize:
                date_text = normalize_date(date_text, pattern)["date"]

            stripped_line = line.strip()

            if stripped_line.startswith(date_text):
                date_position = 'start'
            elif stripped_line.endswith(date_text):
                date_position = 'end'
            else:
                date_position = 'middle'

            break

    return {
        "date_found": date_found,
        "position": date_position,
        "date_text": date_text
    }


# TODO: fix this
def normalize_date(date_text, pattern):
    date_text = date_text.lower().strip()
    precision = 'unknown'

    # "Jahr – bis heute" (e.g., "2020 - heute")
    if pattern == DATE_PATTERNS[0]:
        year_match = re.search(r'\b\d{4}\b', date_text)
        if year_match:
            year = year_match.group()
            precision = 'year'
            return {"date": f"{year} - Heute", "precision": precision}

    # "Jahr – bis heute" mit "bis" (e.g., "2020 - bis heute")
    elif pattern == DATE_PATTERNS[1]:
        year_match = re.search(r'\b\d{4}\b', date_text)
        if year_match:
            year = year_match.group()
            precision = 'year'
            return {"date": f"{year} - Heute", "precision": precision}

    # "Jahr zu Jahr" (e.g., "2004 - 2008")
    elif pattern in [DATE_PATTERNS[2], DATE_PATTERNS[3]]:
        years = re.findall(r'\d{4}', date_text)
        if len(years) == 2:
            precision = 'year'
            return {"date": f"{years[0]} - {years[1]}", "precision": precision}

    # "Monat/Jahr – Monat/Jahr" (e.g., "03/2018 – 07/2018")
    elif pattern == DATE_PATTERNS[4]:
        try:
            start, end = date_text.split("–")
            start_obj = dateparser.parse(start.strip())
            end_obj = dateparser.parse(end.strip()) if "heute" not in end.strip().lower() else None
            
            if start_obj:
                start_formatted = start_obj.strftime('%m.%Y') if start_obj.day == 1 else start_obj.strftime('%d.%m.%Y')
                precision = 'month' if start_obj.day == 1 else 'day'
            else:
                return {"date": "Invalid date format", "precision": precision}

            if end_obj:
                end_formatted = end_obj.strftime('%m.%Y') if end_obj.day == 1 else end_obj.strftime('%d.%m.%Y')
            else:
                end_formatted = "Heute"
                
            return {"date": f"{start_formatted} - {end_formatted}", "precision": precision}

        except (ValueError, AttributeError):
            return {"date": "Invalid date format", "precision": precision}

    # TODO: add for more formats ..

    return {"date": date_text, "precision": precision}


def handle_start_date(current_point, date, description, structured_points):
    if current_point:
        structured_points.append(current_point)

    current_point = {
        "date": date,
        "description": description.strip()
    }
    return current_point


def handle_middle_date(current_point, description):
    # TODO
    if current_point:
        current_point["description"] += " " + description
    return current_point


def handle_end_date(current_point, date, description, structured_points):
    if current_point:
        current_point["description"] += " " + description.strip()
        structured_points.append(current_point)

    current_point = {"date": date, "description": description.strip()}
    return current_point
    

def handle_start_date_work(current_point, date, description, company_name, structured_points):
    if current_point:
        structured_points.append(current_point)

    current_point = {
        "date": date,
        "company_name": company_name,
        "description": description.strip()
    }
    return current_point


def get_company_name(line, experience_points, i, company_name_pattern):
    company_name = ""
    if i + 1 < len(experience_points):
        next_line = experience_points[i + 1].strip()
        firm_match = re.search(company_name_pattern, next_line)
        if firm_match:
            company_name = firm_match.group(0).strip()
    return company_name


def get_milestones(text, is_work_experience = False):
    experience_points = text.splitlines()  
    structured_points = []
    current_point = None
    company_name = ""
    job_title = ""

    for i, line in enumerate(experience_points):
        result = check_date_position(line, False)

        if result['date_found']:
            date = result['date_text']
            date_position = result['position']
            description = line.replace(date, '').strip()

            company_name = get_company_name(line, experience_points, i, COMPANY_NAME_PATTERN) if is_work_experience else ""

            if date_position == 'start':
                if is_work_experience:
                    current_point = handle_start_date_work(current_point, date, description, company_name, structured_points)
                else:
                    current_point = handle_start_date(current_point, date, description, structured_points)

            elif date_position == 'end':
                current_point = handle_end_date(current_point, date, description, structured_points)

            elif date_position == 'middle':
                current_point = handle_middle_date(current_point, description)

        else:
            if current_point:
                if is_work_experience:
                    current_point["description"] += " " + line.replace(company_name, '').strip()
                else:
                    current_point["description"] = line.strip()


    if current_point:
        structured_points.append(current_point)

    return structured_points


def save_to_json(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


def extract_work(text_block):
    result = get_milestones(text_block, True)
    return result


def extract_education(text_block):
    result = get_milestones(text_block)
    return result



# save code-list into dictionary
def extract_codeList(file_path):

    pdf_text = ""
    with fitz.open(file_path) as pdf:
        for page_num in range(pdf.page_count):
            pdf_text += pdf[page_num].get_text()

    lines = pdf_text.split('\n')

    
    data = defaultdict(list)
    current_heading = None
    current_sub_heading = None
    last_bezeichnung = None

    # define mask to extract the name and the code
    heading_pattern = re.compile(r"^\d+\.\s+(.+)$")
    sub_heading_pattern = re.compile(r"^A\d{3}\s*–\s*A\d{3}$")
    code_pattern = re.compile(r"A\d{3}$")


    for line in lines:
        text = line.strip()


        if not text:
            continue

        heading_match = heading_pattern.match(text)
        if heading_match:
            current_heading = heading_match.group(1)
            current_sub_heading = None # revert subheading
            last_bezeichnung = None
            continue

        if sub_heading_pattern.match(text):
            current_sub_heading = f"{current_heading} ({last_bezeichnung}: {text})"
            data[current_sub_heading] = []

            last_bezeichnung = None
            continue

        if code_pattern.match(text):

            if last_bezeichnung:
                entry = {"Bezeichnung": last_bezeichnung, "Code": text}

                if current_sub_heading:
                    data[current_sub_heading].append(entry)
                elif[current_heading]:
                    data[current_heading].append(entry)

                last_bezeichnung = None
            continue

        last_bezeichnung = text
    return dict(data)


code_file_path = ""
parsed_data = extract_codeList(code_file_path)
print(parsed_data)
