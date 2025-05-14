import fitz
from extract_milestones import extract_education, extract_work
import os
import itertools


# TODO Mabye define Stopwords in .txt or Json File

WORK_HEADING_SET = {
    'arbeitserfahrung',
    'arbeitserfahrungen',
    'berufliche',
    'erfahrung',
    'erfahrungen',
    #'skills',
    'beruflicher',
    'werdegang',
    'berufserfahrung',
    'berufserfahrungen'
}

EDUCATION_HEADING_SET = {
    "ausbildung",
    "ausbildungsweg",
    "schulische",
    "schulbildung",
    "studium",
    "schul",
    "berufsausbildung",
    "berufliche",
    "weiterbildung",
    "beruflicher",
    "weiterbildungen",
    "weiterbildung",
    "seminare",
    "bildung",
    "bildungsgang",
    "schulausbildung",
    "berufsbildung"
}

DIVERSE_HEADING_SET = {
    'besondere',
    'diverses',
    'ehrenamt',
    'erfahrungen',
    'fach',
    'fachkompetenzen',
    'fähigkeiten',
    'it',
    'kenntnisse',
    'kompetenzen',
    'persönliche',
    'professional',
    'qualifikationen',
    'skills',
    'sonstige',
    'sonstiges',
    'sprachkenntnisse',
    'themen',
    'themenkompetenzen',
    'tätigkeiten',
    'weitere',
    'zusatzqualifikationen',
    'edv',
    'ikt',
    'zusatzausbilundungen',
    'it'
}

STOPWORDS = {
    'und',
    'oder',
    '&',
    '/',
    '-',
    'sowie',
    'auch',
    ' ',
    '(in', 
    'abfallender', 
    'reihenfolge):',
    ':',
    ''}

def extract_headings(blocks: list, headings_set: set) -> list[dict]:
    """
    Iterates over given blocks and extracts lines of text that qualify as relevant headings (all words in predefined sets).
    """
    results = []
    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    # Get span information
                    text = span["text"]
                    font = span["font"]
                    font_size = span["size"]
                    is_bold = "Bold" in font
                    is_italic = "Italic" in font
                    color = span["color"]

                    # Check if span text may be given heading
                    text_list = text.replace("-", " ").strip().lower().split(" ")
                    text_set = set(text_list)
                    if text_set.issubset(headings_set.union(STOPWORDS)):
                        if(len(text_list) < 2):
                            if(text_list[0] in STOPWORDS):
                                continue

                        results.append({
                            "text": text,
                            "font": font,
                            "font_size": font_size,
                            "bold": is_bold,
                            "italic": is_italic,
                            "color": color
                        })
    return results


def has_same_styling(a: dict, b: dict = None, span : dict = None) -> bool:
    """
    Compares a custom span dict with another custom span dict or a given fitz span.
    """
    if b is None:
        # compare with SPAN dict
        return a["font"] == span["font"] and a["font_size"] == span["size"] and a["bold"] == ("Bold" in span["font"]) and a["italic"] == ("Italic" in span["font"]) and a["color"] == span["color"]

    # compare with custom defined dict
    return a["font"] == b["font"] and a["font_size"] == b["font_size"] and a["bold"] == b["bold"] and a["italic"] == b["italic"] and a["color"] == b["color"]


# TODO: Maybe solve differently. If each list happen to contain non-heading lines, the wrong style may be extracted
def match_extracted_headings(work: list[dict], education: list[dict], diverse: list[dict]) -> tuple[list[dict], list[dict], list[dict], dict]:
    """
    Extracts a common styling (styling of headings) between the given text lines and discards lines with different style.
    """
    styles = dict()
    all_combinations = itertools.product(work, education, diverse)
    if len(work) == 0:
        if len(education) == 0:
            if len(diverse) == 0:
                # TODO no heading found
                return None, None, None, None
            
            else:
                return None, None, diverse, {"font": diverse[0]["font"],
                            "font_size": diverse[0]["font_size"],
                            "bold": diverse[0]["bold"],
                            "italic": diverse[0]["italic"],
                            "color": diverse[0]["color"]}
            
        elif len(diverse) == 0:
            return None, education, None, {"font": education[0]["font"],
                            "font_size": education[0]["font_size"],
                            "bold": education[0]["bold"],
                            "italic": education[0]["italic"],
                            "color": education[0]["color"]}
        
        else:
            # compare education and diverse headings
            for e in education:
                for d in diverse:
                    equal = True and (e["font"] == d["font"])
                    equal = equal and (e["font_size"] == d["font_size"])
                    equal = equal and (e["bold"] == d["bold"])
                    equal = equal and (e["italic"] == d["italic"])
                    equal = equal and (e["color"] == d["color"])
                        
                    if equal:
                        styles = {
                            "font": e["font"],
                            "font_size": e["font_size"],
                            "bold": e["bold"],
                            "italic": e["italic"],
                            "color": e["color"]
                        }

    elif len(education) == 0:
        if len(diverse) == 0:
            return work, None, None, {"font": work[0]["font"],
                            "font_size": work[0]["font_size"],
                            "bold": work[0]["bold"],
                            "italic": work[0]["italic"],
                            "color": work[0]["color"]}
        else:
            # compare work and diverse heading
            for w in work:
                for d in diverse:
                    equal = True and (w["font"] == d["font"])
                    equal = equal and (w["font_size"] == d["font_size"])
                    equal = equal and (w["bold"] == d["bold"])
                    equal = equal and (w["italic"] == d["italic"])
                    equal = equal and (w["color"] == d["color"])
                        
                    if equal:
                        styles = {
                            "font": w["font"],
                            "font_size": w["font_size"],
                            "bold": w["bold"],
                            "italic": w["italic"],
                            "color": w["color"]
                        }
            
    elif len(diverse) == 0:
        for w in work:
            for e in education:
                # Check if styling of all headings are equal
                equal = True and (w["font"] == e["font"])
                equal = equal and (w["font_size"] == e["font_size"])
                equal = equal and (w["bold"] == e["bold"])
                equal = equal and (w["italic"] == e["italic"])
                equal = equal and (w["color"] == e["color"])
                    
                if equal:
                    styles = {
                        "font": w["font"],
                        "font_size": w["font_size"],
                        "bold": w["bold"],
                        "italic": w["italic"],
                        "color": w["color"]
                    }
    else:
        for w in work:
            for e in education:
                for d in diverse:
                    # Check if styling of all headings are equal
                    equal = True and (w["font"] == e["font"] == d["font"])
                    equal = equal and (w["font_size"] == e["font_size"] == d["font_size"])
                    equal = equal and (w["bold"] == e["bold"]  == d["bold"])
                    equal = equal and (w["italic"] == e["italic"] == d["italic"])
                    equal = equal and (w["color"] == e["color"] == d["color"])
                    
                    if equal:
                        styles = {
                            "font": w["font"],
                            "font_size": w["font_size"],
                            "bold": w["bold"],
                            "italic": w["italic"],
                            "color": w["color"]
                        }
    if not equal:
        return {}, {}, {}, None

    # Remove lines that are not styled as headings
    remove_list = []
    for w in work:
        if not has_same_styling(w, b=styles):
            remove_list.append(w)
    work_res = [w for w in work if w not in remove_list]
    remove_list = []
    
    for e in education:
        if not has_same_styling(e, b=styles):
            remove_list.append(e)
    education_res = [e for e in education if e not in remove_list]
    remove_list = []
    
    for d in diverse:
        if not has_same_styling(d, b=styles):
            remove_list.append(d)
    diverse_res = [d for d in diverse if d not in remove_list]
    
    return work_res, education_res, diverse_res, styles


def extract(path: str) -> tuple[list[dict], list[dict], list[dict], dict] | int:
    """
    Extracts headings for work experience, education and other experience.
    """
    doc = fitz.open(path)
    results_work = []
    results_education = []
    results_diverse = []
    empty_counter = 0
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                continue
            else:
                empty_counter += 1
                if empty_counter == len(blocks):
                    return 0     
        results_work.extend(extract_headings(blocks, WORK_HEADING_SET))
        results_education.extend(extract_headings(blocks, EDUCATION_HEADING_SET))
        results_diverse.extend(extract_headings(blocks, DIVERSE_HEADING_SET))
    doc.close()

    res = match_extracted_headings(results_work, results_education, results_diverse)

    # TODO: Maybe keep doc open and extract strings (function extract_text_segments) here

    return res


def is_relevant_heading(span: dict, headings_list: list[dict]) -> bool:
    """
    Check if given span is in extracted headings list.
    """
    for h in headings_list:
        if h["text"] == span["text"]:
            return True
    return False


def extract_text_segments(path: str, work_headings: list[dict], education_headings: list[dict], diverse_headings: list[dict], headings_style: dict) -> tuple[str, str, str]:
    """
    Extracts text in segments that have given headings.
    """
    doc = fitz.open(path)
    work_list = []
    def _process_work(text):
        if len(text) <= 1:
            work_list.append("\n")
        else:
            work_list.append(text)
    
    education_list = []
    def _process_education(text):
        if len(text) <= 1:
            education_list.append("\n")
        else:
            education_list.append(text)
            
    diverse_list = []
    def _process_diverse(text):
        if len(text) <= 1:
            diverse_list.append("\n")
        else:
            diverse_list.append(text)
    
    process_func = lambda x: None
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if has_same_styling(headings_style, span=span):
                            if is_relevant_heading(span, work_headings):
                                process_func = _process_work
                            elif is_relevant_heading(span, education_headings):
                                process_func = _process_education
                            elif is_relevant_heading(span, diverse_headings):
                                process_func = _process_diverse
                            else:
                                # If there is a heading (according to style) that is not relevant, do not extract information
                                process_func = lambda x: None
                        process_func(span["text"])
    doc.close()
    
    work_str = " ".join(work_list)
    education_str = " ".join(education_list)
    diverse_str = " ".join(diverse_list)
    return work_str, education_str, diverse_str


def main():
    folder = rf'C:\Users\jopre\Documents\TRESCON\trescon_download\download'
    failed_counter = 0
    no_work = 0
    no_education = 0
    no_diverse = 0
    no_heading = 0
    no_content = 0
    no_work_extracted = 0
    no_education_extracted = 0
    #'''
    for i, filename in enumerate(os.listdir(folder)):
        try:
            if i == 14000:
                break
            if filename.endswith(".pdf"):
                res = extract(f'{folder}/{filename}')
                if type(res) == int:
                    print(f'File {filename} is not readable.')
                    no_content += 1
                else: 
                    work = res[0]
                    education = res[1]
                    diverse = res[2]
                    styles = res[3]   
                    if work is None and education is None and diverse is None and styles is None:
                        print(f'No heading found in {filename}.')
                        no_heading += 1
                    elif styles is None:
                        print(f'No stlye matching found in {filename}.')
                        failed_counter += 1
                    elif work is None:
                        print(f'No work in {filename}.')
                        no_work += 1
                    elif education is None:
                        print(f'No education in {filename}.')
                        no_education += 1
                    elif diverse is None:
                        print(f'No diverse in {filename}.')  
                        no_diverse +=1
                    else:
                        work_str, education_str, diverse_str = extract_text_segments(f'{folder}/{filename}', work, education, diverse, styles)

                        # print(extract_work(work_str))
                        # print("==============================================================================")
                        if not extract_work(work_str):
                            print(f'Not possible to extract work in {filename}')
                            no_work_extracted += 1

                        # print(extract_education(education_str))
                        # print("==============================================================================")
                        if not extract_education(education_str):
                            print(f'Not possible to extract education in {filename}')
                            no_education_extracted += 1

                
                    

        except Exception as e:
            print(e)
    '''
    for i, filename in enumerate(os.listdir(folder)):        
        if i == 1000:
            break
        if filename.endswith(".pdf"):
            work, education, diverse, styles = extract(f'spd2_trescon/TRESCON/trescon_download/download/{filename}')
            if work is None:
                print(f'No heading found in {filename}.')
            if styles is None:
                print(f'No stlye matching found in {filename}.')
                failed_counter += 1
            elif work is None:
                print(f'no work in{filename}.')
                no_work += 1
            elif education is None:
                print(f'no education in{filename}.')
                no_education += 1
            elif diverse is None:
                print(f'no diverse in{filename}.')  
                no_diverse +=1
            else:
                work_str, education_str, diverse_str = extract_text_segments(f'spd2_trescon/TRESCON/trescon_download/download/{filename}', work, education, diverse, styles)  
    '''  
    print("==============================================================")
    #print(f'In {len(os.listdir(folder))} documents:')             
    print(f'In 14000 documents:') 
    print(f'{no_content} files can not be read.')
    print(f'The style finder failed {failed_counter} times.')
    print(f'No work was found {no_work} times.')
    print(f'No education was found {no_education} times.')
    print(f'No diverse was found {no_diverse} times.')
    print(f'No heading was found {no_heading} times.')
    print(f'Not possible to extract education {no_education_extracted} times.')
    print(f'Not possible to extract work {no_work_extracted}.')


def test_single():
    # filename = '000019622.2010_10_06_Lebenslauf_DI_Fritz.pdf'
    # path = rf'C:\Users\jopre\Documents\TRESCON\trescon_download\download'
    filename = 'document (1).pdf'
    path = rf'C:\Users\jopre\Documents\TRESCON\cvs'    
    res = extract(f'{path}\{filename}')
    if type(res) == int:
        print(f'File {filename} is not readable.')
    else:    
        work = res[0]
        education = res[1]
        diverse = res[2]
        styles = res[3]

        if work is None and education is None and diverse is None and styles is None:
            print(f'No heading found in {filename}.')
        elif styles is None:
            print(f'No stlye matching found in {filename}.')
        elif work is None:
            print(f'No work in{filename}.')
        elif education is None:
            print(f'No education in{filename}.')
        elif diverse is None:
            print(f'No diverse in{filename}.')  
        else:
            work_str, education_str, diverse_str = extract_text_segments(rf'{path}\{filename}', work, education, diverse, styles)
            print(extract_work(work_str))
            print("==============================================================================")
            print(extract_education(education_str))
            print("==============================================================================")
            # print(diverse_str)
            # print("==============================================================================")
        
if __name__ == "__main__":
    main()
    # test_single()
