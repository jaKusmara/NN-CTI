from pathlib import Path

import pandas as pd
import requests

NAME = "kusmara"
MODEL = "llama3:8b"
# MODEL = "llama3:70b"

MODEL_SAFE = MODEL.replace(":", "_")

OUTPUT_DIR = Path(f"outputs_{NAME}_{MODEL_SAFE}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
 
    
INPUT_FILES = [
    "cti-vsp.tsv",
    "cti-ate.tsv",
    "cti-mcq.tsv",
    "cti-rcm.tsv",
    "cti-rcm-2021.tsv",
]

OLLAMA_URL = "http://localhost:11434/api/generate"

for input_file in INPUT_FILES:
    input_path = Path(input_file)
    output_file = OUTPUT_DIR / f"{input_path.stem}-res.csv"

    df = pd.read_csv(input_path, sep="\t")

    print(f"Model: {MODEL} | Input: {input_file} | Starting...")

    first_write = True

    for row in df.itertuples():
        idx = row.Index
        prompt = str(row.Prompt)
        gt = getattr(row, "GT", "")

        print(f"[{input_file}] i={idx}")

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=300
            )
            response.raise_for_status()
            answer = response.json().get("response", "").strip()

        except requests.RequestException as e:
            answer = f"ERROR: {e}"
            print(f"Request failed on row {idx}: {e}")

        row_df = pd.DataFrame([{
            "Index": idx,
            "Prompt": prompt,
            "GT": gt,
            "Prediction": answer
        }])

        row_df.to_csv(
            output_file,
            mode="w" if first_write else "a",
            header=first_write,
            index=False,
            encoding="utf-8"
        )

        first_write = False

    print(f"Done. Input: {input_file} | Output: {output_file}")

print("All done.")