from docx2python import docx2python
from tempfile import SpooledTemporaryFile
import pprint

relevant_headings = {
    "Faktoren" : ["Erfolgskritische Faktoren für die Position"],
    "Aufgaben" : ["Aufgaben"],
    "Qualifikationen" : ["Fachliche Qualifikationen und Kompetenzen", "Fachliche Anforderungen"],
    "Persönlichkeit" : ["Persönliche Anforderungen und Kompetenzen", "Persönliche Kompetenz"]
}

other_headings = ["Ausgangssituation & wichtige Informationen zur Position",
                  "Umfeld der Position im Unternehmen",
                  "Arbeits- und Rahmenbedingungen",
                  "Benefits in Ihrem Unternehmen",
                  "Unternehmenskultur und Wertehaltung",
                  "Sonstige Eckdaten",
                ]

qualification_sections = [
    "Fachliche Qualifikationen und Kompetenzen",
    "Formale Ausbildung",
    "Erfahrung",
    "Digitale Kompetenzen",
    "Digitale Kompetenzen & firmeninterne Tools",
    "Sprachen",
    "Führerschein/eigener PKW als unbedingte Voraussetzung",
    "Reisebereitschaft (Radius, Ausmaß, national/international)",
    "Sonstiges",
    "EDV",
]

def is_relevant_heading(text: str, headings: str):
    return any(text in h for h in headings)

def is_other_heading(text: str):
    return text in other_headings

def is_qualification_heading(text: str):
    return text in qualification_sections


def preprocess_text(file: str) -> list:
    text = ""
    with docx2python(file) as docx_content:
        text = docx_content.text
        docx_content.close()
    splitted_text = text.split("\n")
    cleaned_list = [item.replace("--\t", "") for item in splitted_text]
    cleaned_list = [item.replace("\t", "") for item in cleaned_list]
    cleaned_text = [item for item in cleaned_list if item != ""]
    return cleaned_text


def extract_parts(text: list) -> tuple[str, str, str, str, str]:
    position_name = text[1]

    sections = ["Faktoren", "Aufgaben", "Qualifikationen", "Persönlichkeit"]

    section_lists = {section: [] for section in sections}

    def process_line(section, line):
        if section is None:
            return
        if len(line) <= 1:
            section_lists[section].append("\n")
        elif section == "Qualifikationen":
            if is_qualification_heading(line):
                section_lists[section].append(line + "\n")
            else:
                section_lists[section].append("\t" + line + "\n")
        else:
            section_lists[section].append(line + "\n")

    current_section = None
    for line in text:
        for section in sections:
            if is_relevant_heading(line, relevant_headings[section]):
                current_section = section
            elif is_other_heading(line):
                current_section = None
        process_line(current_section, line)
    
    factor_str = "".join(section_lists["Faktoren"])
    task_str = "".join(section_lists["Aufgaben"])
    qualification_str = "".join(section_lists["Qualifikationen"])
    personality_str = "".join(section_lists["Persönlichkeit"])

    return position_name, factor_str, task_str, qualification_str, personality_str


def extract_skills(skill_str: str):
    splitted = skill_str.split("\n")
    skill_results = []
    for skill in splitted:
        if skill:
            if skill not in relevant_headings:
                skill_results.append(skill)
    return skill_results


def extract_personal_skills(skill_str: str):
    not_allowed = [
        "Gewünschtes Alter (von-bis):",
        "Geschlecht:"
        ]
    splitted = skill_str.split("\n")
    skill_results = []
    for skill in splitted:
        add = True
        for x in not_allowed:
            if x in skill or skill in relevant_headings:
                add = False
        if add and skill:
            skill_results.append(skill)

    return skill_results


def extract_qualifications(skill_str: str):
    relevant_parts = [ "Erfahrung",
                       "Digitale Kompetenzen & firmeninterne Tools",
                       "Sonstiges",
                       "EDV"
                       ]
    splitted = skill_str.split("\n")
    skill_results = []
    for i in range(len(splitted)):
        if any(part in splitted[i] for part in relevant_parts):
            j = i + 1
            while j < len(splitted) and splitted[j].startswith("\t"):
                skill_results.append(splitted[j].strip())
                j += 1

    return skill_results

def extract_education(skill_str: str):
    relevant_parts = ["Formale Ausbildung"]
    splitted = skill_str.split("\n")
    skill_results = []
    for i in range(len(splitted)):
        if any(part in splitted[i] for part in relevant_parts):
            j = i + 1
            while j < len(splitted) and splitted[j].startswith("\t"):
                skill_results.append(splitted[j].strip())
                j += 1

    return skill_results

def extract_requirement(file):
    text = preprocess_text(file)
    position_name, factor_str, task_str, qualification_str, personality_str = extract_parts(text)
    skills_list = [] 
    personal_skills_list = []
    qualification_list = []
    education_list = []
    skills_list.extend(extract_skills(factor_str))
    skills_list.extend(extract_skills(task_str))
    personal_skills_list.extend(extract_personal_skills(personality_str))
    qualification_list.extend(extract_qualifications(qualification_str))
    education_list.extend(extract_education(qualification_str))

    return position_name, skills_list, personal_skills_list, qualification_list, education_list