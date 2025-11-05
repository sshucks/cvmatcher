from typing import Callable
import pandas as pd




applicants = pd.read_csv("validation_data.csv")

for applicant in applicants:
    scores = validate(applicant['requirements'], applicant['cv'], matching_function)

