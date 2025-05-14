import os
import subprocess
from tqdm import tqdm

def process_cvs_with_php(input_directory, output_directory, php_script_path):
    os.makedirs(output_directory, exist_ok=True)
    print("Starting CV extraction ...")

    for filename in tqdm(os.listdir(input_directory)):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(input_directory, filename)
            output_file = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}_processed.json")

            try:
                result = subprocess.run(
                    ["php", php_script_path, file_path, output_file],
                    check=True,
                    capture_output=True,
                    text=True
                )

            except subprocess.CalledProcessError as e:
                print(f"Error processing {file_path}: {e.stderr}")

    print("CV extraction completed.")

def process_cvs(input_dir, output_dir, php_script):

    if not os.path.exists(php_script):
        print(f"Error: PHP script not found at {php_script}")
    else:
        print(f"PHP script found at {php_script}")

    process_cvs_with_php(input_dir, output_dir, php_script)


