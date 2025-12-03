from parse_requirements.esco.translate_requirements import ESCOTranslateRequirements
from parse_cv.esco.translate_cv import ESCOEnrichCV, ESCOTranslateCV
from matching.esco.matching import EducationEscoMatchingStep, ExperienceEscoMatchingStep, SkillEscoMatchingStep
from definitions import RequirementsData, CVData
from sentence_transformers import SentenceTransformer
import json
import time


cv = open("llm_extracted/B-1_1.json", "r")
cv = json.load(cv)

args = {"esco_job_threshold":0.8, "esco_skill_threshold":0.8, "esco_education_threshold":0.65, "esco_language":"en"}

cvTranslator = ESCOEnrichCV(args)

start = time.time()
cv = cvTranslator.run(cv, args)
end = time.time()
print(f"CV Translate + Enrich: {end - start}")

json_str = json.dumps(cv, indent=4)
with open("sampleCVEn.json", "w") as f:
    f.write(json_str)



args = {"esco_job_threshold":0.8, "esco_skill_threshold":0.8, "esco_education_threshold":0.65, "esco_language":"en"}

req = open("llm_extracted/B-Stellenbeschreibung_1.json", "r")
req = json.load(req)

reqTranslator = ESCOTranslateRequirements(args)
start = time.time()
req = reqTranslator.run(req, args)
end = time.time()
print(f"Req Translate: {end - start}")

json_str = json.dumps(req, indent=4)
with open("sampleReqEn.json", "w") as f:
    f.write(json_str)



cv_file = open("sampleCVEn.json", "r")
cv = json.load(cv_file)

cv_file.close()

req_file = open("sampleReqEn.json", "r")
req = json.load(req_file)

req_file.close()

args = {"esco_language":"en", "esco_skill_decay":0.8, "esco_job_decay":0.8}


print("\nEducation:")
matcher = EducationEscoMatchingStep(args)
start = time.time()
print(matcher.run(cv["education"], req["education"], args))
end = time.time()
print(f"Matching Education: {end - start}")

print("\nExperience:")
matcher = ExperienceEscoMatchingStep(args)
start = time.time()
print(matcher.run(cv["professional_experience"], req["professional_experience"], args))
end = time.time()
print(f"Matching Experience: {end - start}")

print("\nSoft Skills:")
matcher = SkillEscoMatchingStep(args)
start = time.time()
print(matcher.run(cv["soft_skills"], req["soft_skills"], args))
end = time.time()
print(f"Matching Soft Skills: {end - start}")

print("\nHard Skills:")
matcher = SkillEscoMatchingStep(args)
start = time.time()
print(matcher.run(cv["hard_skills"], req["hard_skills"], args))
end = time.time()
print(f"Matching Hard Skills: {end - start}")


