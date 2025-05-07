import json
import sys
import pprint
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from matching.match_requirements import Model
from extracting.requirements_profile.extract_requirements import extract_requirement


model = Model("google-bert/bert-base-german-cased")

def remove_irelevant_matches(match_dict: dict):
    for key in match_dict.keys():
        if match_dict[key]["Score"] < 0.8:
            match_dict.pop(key)
    return match_dict

def calculate_requirement_embeddings(position_name, skill_list, personal_skills_list, qualification_list, education_requirements):
    position_embeddings = model.get_requirements_embeddings(position_name)
    skill_embeddings = model.get_requirements_embeddings(skill_list)
    personal_embeddings = model.get_requirements_embeddings(personal_skills_list)
    qualification_embeddings = model.get_requirements_embeddings(qualification_list)
    education_embeddings = model.get_requirements_embeddings(education_requirements)

    return position_embeddings, skill_embeddings, personal_embeddings, qualification_embeddings, education_embeddings

def extract_skills(cv_dict):
    skill_list = []
    level_list = []
    for skill in cv_dict["skills"]:
        if skill:
            for s in skill["skill_name"]:
                if s != "" and s:
                    skill_list.append(s)
    return skill_list, level_list            

def extract_work(cv_dict):
    work_list = []
    work_description = []
    for work in cv_dict["employments"]:
        if work:
                if work['position'] != "" and work['position']:
                    work_list.append(work["position"])
                    if work["position_note"] != "" and work['position']:
                        work_description.append(work["position_note"])
    return work_list, work_description

def extract_education(cv_dict):
    education_list = []
    education_institution = []
    for education in cv_dict["education"]:
        if education:
                education_text = education["education_text"]
                if education_text != "" and education_text:
                    education_inst = education["institute"]
                    if education_inst != "" and education_inst:
                        education_list.append(education_text + " " + education_inst)
                        education_institution.append(education["institute"])
    return education_list, education_institution

def get_personal_information(cv_dict):
    personal_information = {"firstname": cv_dict["personal_data"]["firstname"],
                            "surname": cv_dict["personal_data"]["surname"],
                            "birthdate": cv_dict["personal_data"]["birthdate"],
                            "gender": cv_dict["personal_data"]["gender"]}
    
    return personal_information

def compare_work(work_list, requirement_embeddings, position_name):
    position_list = [position_name]
    cv_embeddings = model.get_cv_embeddings(work_list)
    result = model.calculate_match(requirement_embeddings, cv_embeddings, position_list, work_list)
    return result

def compare_skills(skill_list, qualifaction_embeddings, task_embeddings, personal_embeddings,
                   qualification_skills, task_list, personal_skills):
    cv_embeddings = model.get_cv_embeddings(skill_list)
    result_qualification = model.calculate_match(qualifaction_embeddings, cv_embeddings, qualification_skills, skill_list)
    result_tasks = model.calculate_match(task_embeddings, cv_embeddings, task_list, skill_list)
    result_personal = model.calculate_match(personal_embeddings, cv_embeddings, personal_skills, skill_list)
    return result_qualification, result_tasks, result_personal


def compare_education(education_list, requirement_embeddings, qualification_list):
     cv_embeddings = model.get_cv_embeddings(education_list)
     result = model.calculate_match(requirement_embeddings, cv_embeddings, qualification_list, education_list)
     return result

def extract_relevant_skills(skill_result, threshold, penalty):
    cleaned_skills = {}
    for key in skill_result:
        if skill_result[key]["Score"] > threshold:
            cleaned_skills[key] = skill_result[key]
        else:
            cleaned_skills[key] = {"Match" : "penalty",
                                   "Score": penalty}    
    return cleaned_skills

def get_score(result):
    total_score = 0
    for val in result.values():
        score = val["Score"]
        total_score += score
    return total_score / len(result)

def calculate_total_score(work_score, work_weight, 
                          skill_score, skill_weight, 
                          personal_score, personal_weight, 
                          education_score, education_weight):
    total_score = work_score * work_weight + skill_score * skill_weight + personal_score * personal_weight + education_score * education_weight
    return total_score

def calculate_score(applicant_data, requirements_data, 
                    position_name, skill_list, personal_skills_list, qualification_list, education_requirements, 
                    work_weight, skill_weight, personal_weight, education_weight):
    
    json_file = open(applicant_data)    
    cv_dict = json.load(json_file)
    json_file.close()
    work_list, work_description = extract_work(cv_dict)
    profesional_skills, skill_level = extract_skills(cv_dict)
    education_list, education_institution = extract_education(cv_dict)

    # compares position with last jobs
    if work_list:
        work_results = compare_work(work_list, requirements_data[0], position_name) 
        work_score = get_score(work_results)
    else:
        work_score = 0.7

    # compare skills of applicant with formal qualification for the job, personal skills and tasks
    if profesional_skills:
        qualification_results, task_results, personal_results = compare_skills(profesional_skills, requirements_data[3], 
                                                                            requirements_data[1], requirements_data[2], 
                                                                            qualification_list, skill_list, personal_skills_list)

        relevant_qualification_results = extract_relevant_skills(qualification_results, 0.8, 0.5)
        relevant_task_results = extract_relevant_skills(task_results, 0.83, 0.6)
        relevant_personal_results = extract_relevant_skills(personal_results, 0.8, 0.5)

        qualification_score = get_score(relevant_qualification_results)
        task_score = get_score(relevant_task_results)
        skill_score = qualification_score * 0.65 + task_score * 0.35
        personal_score = get_score(relevant_personal_results)
    
    else:
        skill_score = 0.7
        personal_score = 0.7

    #compare education with formal qualification
    if education_list:
        education_results = compare_education(education_list, requirements_data[4], education_requirements)
        education_score = get_score(education_results)
    else:
        education_score = 0.7

    final_score = calculate_total_score(work_score, work_weight, skill_score, skill_weight, 
                                        personal_score, personal_weight, education_score, education_weight)
    personal_information = get_personal_information(cv_dict)
    return {"Name": personal_information["firstname"] + " " + personal_information["surname"],
            "Gender": personal_information["gender"],
            "Birthdate": personal_information["birthdate"],
            "Score": final_score}

def match_applicant(file, work_weight, skill_weight, personal_weight, education_weight, n):
    print(type(file))
    score_dict = {}
    total_weights = work_weight + skill_weight + personal_weight + education_weight
    work_weight = work_weight / total_weights
    skill_weight = skill_weight / total_weights
    personal_weight = personal_weight / total_weights
    education_weight = education_weight / total_weights
    position_name, skill_list, personal_skills_list, qualification_list, education_requirements = extract_requirement(file.file)
    requirements_data = calculate_requirement_embeddings(position_name, 
                                                                                                                        skill_list,
                                                                                                                        personal_skills_list, 
                                                                                                                        qualification_list, 
                                                                                                                education_requirements)
    score_dict = {}
    try:
        for i, applicant in enumerate(sorted(os.listdir("./code/matching/TRESCON/cv_dicts/"))):
            try:
                score = calculate_score("./code/matching/TRESCON/cv_dicts/" + applicant, requirements_data, 
                                        position_name, skill_list, personal_skills_list, qualification_list, education_requirements,
                                        work_weight, skill_weight, personal_weight, education_weight)
                #print(score)
                score_dict[score["Name"]] = {"Score": score["Score"],
                                         "Birthdate": score["Birthdate"],
                                         "Filename": applicant} 
            except Exception as e:
                print(f"Calculation for {applicant} did not work because {e}")    
    
        result_df = pd.DataFrame.from_dict(score_dict, orient='index', columns=['Score', 'Birthdate', 'Filename']).reset_index()
        result_df.rename(columns={'index': 'Name'}, inplace=True)
        result_df = result_df.sort_values(by='Score', ascending=False).head(n)    
        return result_df
    except Exception as e:
        print(e) 
