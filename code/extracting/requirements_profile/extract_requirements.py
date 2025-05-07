from docx2python import docx2python
from tempfile import SpooledTemporaryFile
import pprint


relevant_headings = ["Erfolgskritische Faktoren für die Position",
                     "Aufgaben",
                     "Fachliche Qualifikationen und Kompetenzen",
                     "Persönliche Anforderungen und Kompetenzen",
                     "Persönliche Kompetenz"
                    ]

other_headings = ["Ausgangssituation & wichtige Informationen zur Position",
                  "Umfeld der Position im Unternehmen",
                  "Arbeits- und Rahmenbedingungen",
                  "Benefits in Ihrem Unternehmen",
                  "Unternehmenskultur und Wertehaltung",
                  "Sonstige Eckdaten",
                ]

qualification_parts = ["Fachliche Qualifikationen und Kompetenzen",
                       "Formale Ausbildung",
                       "Erfahrung",
                       "Digitale Kompetenzen & firmeninterne Tools",
                       "Sprachen",
                       "Führerschein/eigener PKW als unbedingte Voraussetzung",
                       "Reisebereitschaft (Radius, Ausmaß, national/international)",
                       "Sonstiges",
                       "EDV"
                       ]


def is_relevant_heading(text: str, heading: str):
    if text == heading:
        return True
    return False


def is_other_heading(text: str):
    for h in other_headings:
        if h == text:
            return True
    return False


def is_qualification_heading(text: str):
    for h in qualification_parts:
        if h == text:
            return True
    return False


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
    factor_list = []
    position_name = text[1]
    def _process_factors(text):
        if len(text) <= 1:
            factor_list.append("\n")
        else:
            factor_list.append(text + "\n")
        
    task_list = []
    def _process_task(text):
        if len(text) <= 1:
            task_list.append("\n")
        else:
            task_list.append(text + "\n")
                
    qualifictaion_list = []
    def _process_qualification(text):
        if len(text) <= 1:
            qualifictaion_list.append("\n")
        else:
            if is_qualification_heading(text):
                qualifictaion_list.append(text + "\n")
            else:
                qualifictaion_list.append("\t" + text + "\n")

    personality_list = []
    def _process_personality(text):
        if len(text) <= 1:
            personality_list.append("\n")
        else: 
            personality_list.append(text + "\n")

    process_func = lambda x: None
    for line in text:
        if is_relevant_heading(line, relevant_headings[0]):
            process_func = _process_factors
        elif is_relevant_heading(line, relevant_headings[1]):
            process_func = _process_task
        elif is_relevant_heading(line, relevant_headings[2]):
            process_func = _process_qualification
        elif is_relevant_heading(line, relevant_headings[3]):
            process_func = _process_personality
        elif is_relevant_heading(line, relevant_headings[4]):
            process_func = _process_personality
        elif is_other_heading(line):
            process_func = lambda x: None
        process_func(line)

        
    factor_str = "".join(factor_list)
    task_str = "".join(task_list)
    qualification_str = "".join(qualifictaion_list)
    personality_str = "".join(personality_list)

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
        if splitted[i] in relevant_parts:
            j = i + 1
            while j < len(splitted) and splitted[j].startswith("\t"):
                skill_results.append(splitted[j].strip())
                j += 1

    return skill_results

def extract_eductaion(skill_str: str):
    relevant_parts = ["Formale Ausbildung"]
    splitted = skill_str.split("\n")
    skill_results = []
    for i in range(len(splitted)):
        if splitted[i] in relevant_parts:
            j = i + 1
            while j < len(splitted) and splitted[j].startswith("\t"):
                skill_results.append(splitted[j].strip())
                j += 1

    return skill_results

def extract_requirement(file: SpooledTemporaryFile):
    text = preprocess_text(file)
    extracted = extract_parts(text)
    skills_list = [] 
    personal_skills_list = []
    qualification_list = []
    education_list = []
    skills_list.extend(extract_skills(extracted[1]))
    skills_list.extend(extract_skills(extracted[2]))
    personal_skills_list.extend(extract_personal_skills(extracted[4]))
    qualification_list.extend(extract_qualifications(extracted[3]))
    education_list.extend(extract_eductaion(extracted[3]))
    return extracted[0], skills_list, personal_skills_list, qualification_list, education_list
    