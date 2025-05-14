import json
import os
import pprint
from tqdm import tqdm
import copy

CV_STRUCTURE = {
    'personal_data': 
    {
    },
    'employments': [
    ],
    'education': [
    ],
    'skills': [
    ],
    'language': [
    ]
}


def extract_personal_data(data, cv):
    cv['personal_data']['firstname'] = data['Firstname']
    cv['personal_data']['surname'] = data['Surname']
    cv['personal_data']['birthdate'] = data['Birth_Date']
    cv['personal_data']['gender'] = 'f' if data['Is_Female'] else 'm'
    cv['personal_data']['postal_code'] = data['Postal_Code']
    cv['personal_data']['country_code'] = data['TEXT_Country_Code']
    return cv


def extract_employments(data, cv):
    employment_data = data['Employment']
    for entry in employment_data:
        employment = {'position': entry['Position'], 'position_note': entry['Note']}
        cv['employments'].append(employment)

    return cv

def extract_education(data, cv):
    education_data = data['Person_Education']
    for entry in education_data:
        education = {'education_text': entry['TEXT_Education'], 'institute': entry['TEXT_Institute']}
        cv['education'].append(education)

    return cv

def extract_skills(data, cv):
    skill_data = data['Person_Addition']
    for entry in skill_data:
        skill = {'skill_name': entry['names'], 'skill_level': entry['degree']}
        cv['skills'].append(skill)

    return cv

def extract_languages(data, cv):
    language_data = data['Person_Language']
    for entry in language_data:
        language = {'language_name': entry['TEXT_Language'], 'language_level': entry['TEXT_LNG_Degree']}
        cv['language'].append(language)

    return cv

def extract_data(data, cv):
    cv = extract_personal_data(data, cv)
    cv = extract_employments(data, cv)
    cv = extract_education(data, cv)
    cv = extract_skills(data, cv)
    cv = extract_languages(data, cv)
    return cv

def read_jsons(dir):
    cvs = dict()

    for filename in tqdm(os.listdir(dir)):
        if filename.endswith('json'):
            with open(os.path.join(dir, filename), 'r') as f:
                cv = copy.deepcopy(CV_STRUCTURE)
                cv_data = json.load(f)['data']
                cv = extract_data(cv_data, cv)
                
            cvs[filename] = cv

    return cvs

def save_cvs(cvs, dir):
    if not os.path.exists(dir):
        os.makedirs(dir) 

    for key, cv in cvs.items():
        #                               prevent '.json.json'
        filename = os.path.join(dir, f"{key.removesuffix('.json')}.json")
        with open(filename, 'w') as json_file:
            json.dump(cv, json_file, indent=4)

    
def read_json(input_dir, output_dir):
    print("Starting CV preprocessing ...")
    cvs = read_jsons(input_dir)
    save_cvs(cvs, output_dir)
    print("CV preprocessing completed.")
