from typing import Callable
import pandas as pd

def validate(requirements_path, cv_path, matching_function: Callable, parse_requirements: Callable = None, parse_cv: Callable = None):
    if parse_requirements is not None:
        requirements = parse_requirements(requirements_path)
    
    if parse_cv is not None:
        cvs = parse_cv(cv_path)

    return matching_function(requirements, cvs)


applicants = pd.read_csv("validation_data.csv")

for applicant in applicants:
    scores = validate(applicant['requirements'], applicant['cv'], matching_function)

