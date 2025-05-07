from read_json import read_json
from cv.process_cvs import process_cvs

def main():
    process_cvs("./code/input_cvs", "./code/extracting/cv/extracted_cvs", "./code/extracting/cv/curlRequest.php")
    read_json("./code/extracting/cv/extracted_cvs", "./code/matching/TRESCON/cv_dicts/")


if __name__ == "__main__":
    main()
