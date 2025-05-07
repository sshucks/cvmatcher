from read_json import read_json
from cv.process_cvs import process_cvs
from config import CV_INPUT_DIR, CV_OUTPUT_DIR, CV_OUTPUT_DIR_MATCHING

def main():
    process_cvs(CV_INPUT_DIR, CV_OUTPUT_DIR, "./code/extracting/cv/curlRequest.php")
    read_json(CV_OUTPUT_DIR, CV_OUTPUT_DIR_MATCHING)


if __name__ == "__main__":
    main()
