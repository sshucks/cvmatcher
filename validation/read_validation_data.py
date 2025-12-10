import os
import pandas as pd
from config import VALIDATION_DATA_DIR

folder_map = {
        "ABS":  {"t1": 0, "t2": 0, "grat": 0},
        "T1":   {"t1": 1, "t2": 0, "grat": 0},
        "T2":   {"t1": 1, "t2": 1, "grat": 0},
        "GRAT": {"t1": 1, "t2": 1, "grat": 1},
    }

entries = []

for dir in os.listdir(VALIDATION_DATA_DIR):

    dir_path = os.path.join(VALIDATION_DATA_DIR, dir, "raw_data")

    if not os.path.exists(dir_path):
        continue

    requirements = next(
        (os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith(".docx")),
        None
    )

    if requirements is None:
        print(f"No requirements file found in directory: {dir_path}")
        pass

    for folder, flags in folder_map.items():
        folder_path = os.path.join(dir_path, folder)
        if not os.path.exists(folder_path):
            print(f"No {folder} directory found in: {dir_path}")
            continue

        for file in os.listdir(folder_path):
            if file.endswith(".pdf"):
                entries.append({
                    "requirements_path": requirements,
                    "cv_path": os.path.join(folder_path, file),
                    **flags
                })

df = pd.DataFrame(entries)

df.to_csv("data/validation_data/validation_data.csv", index=False)
print("File saved")