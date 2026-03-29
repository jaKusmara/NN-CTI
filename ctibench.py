import pandas as pd
import requests

MODEL = "llama3"
INPUT_FILE = "cti-mcq.tsv"
OUTPUT_FILE = "outputs/cti-mcq-results.csv"

df = pd.read_csv(INPUT_FILE, sep="\t")
results = []

print(f"Model: {MODEL}\tInput: {INPUT_FILE}\tStarting...")

for idx, row in df.iterrows():
    prompt = row["Prompt"]

    print(f"{idx}\tPrompt: {prompt}\n")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    response.raise_for_status()
    answer = response.json()["response"]

    results.append({
        "Prompt": prompt,
        "GT": row.get("GT", ""),
        "Prediction": answer
    })

pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
print("Hotovo.")