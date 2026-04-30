import os
import re
import pandas as pd
from pathlib import Path

# ==========================================
# Preprocessing Functions
# ==========================================

def format_rcm(text):
    text = str(text)
    cwe_pattern = r'CWE-\d+'
    matches = re.findall(cwe_pattern, text)
    if matches:
        return matches[-1] 
    return text

def format_vsp(text):
    text = str(text)
    cvss_pattern = r'AV:[A-Za-z]+/AC:[A-Za-z]+/PR:[A-Za-z]+/UI:[A-Za-z]+/S:[A-Za-z]+/C:[A-Za-z]+/I:[A-Za-z]+/A:[A-Za-z]+'
    matches = re.findall(cvss_pattern, text)
    if matches:
        return matches[-1] 
    return text

def format_mcq(text):
    text = str(text)
    lines = [line.rstrip() for line in text.split('\n') if line.strip()]
    if not lines:
        return text
    
    last_line = lines[-1]
    
    if last_line.startswith(('A)', 'B)', 'C)', 'D)')):
        return last_line[0]
    if last_line.endswith(('A', 'B', 'C', 'D')):
        return last_line[-1]
    if last_line.endswith('**'):
        return last_line[-3]
        
    return ' '.join(text.split('\n'))

def format_taa(text):
    text = str(text)
    return ' '.join(text.split('\n'))

def format_ate(text):
    text = str(text)
    pattern = r'T\d{4}'
    
    # Try the last line first
    lines = [line for line in text.split('\n') if line.strip()]
    if lines:
        last_line_matches = re.findall(pattern, lines[-1])
        if last_line_matches:
            seen = set()
            unique_matches = [x for x in last_line_matches if not (x in seen or seen.add(x))]
            return ', '.join(unique_matches)
            
    # Fallback: search entire text
    all_matches = re.findall(pattern, text)
    if all_matches:
        seen = set()
        unique_matches = [x for x in all_matches if not (x in seen or seen.add(x))]
        return ', '.join(unique_matches)
        
    return text

# ==========================================
# Main Processing Logic
# ==========================================

INPUT_DIR = Path("outputs")
OUTPUT_DIR = Path("PREPROCESSED_outputs")

def process_files():
    if not INPUT_DIR.exists():
        print(f"Error: Could not find the input directory '{INPUT_DIR}'")
        return

    # Find all CSV files recursively
    csv_files = list(INPUT_DIR.rglob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in '{INPUT_DIR}'")
        return

    for file_path in csv_files:
        # Maintain folder structure but change the extension to .tsv
        rel_path = file_path.relative_to(INPUT_DIR).with_suffix('.tsv')
        out_path = OUTPUT_DIR / rel_path
        
        # Ensure the output subdirectory exists
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Processing: {rel_path} ...", end=" ")
        
        try:
            df = pd.read_csv(file_path)
            
            if 'Prediction' not in df.columns:
                print("SKIPPED (No 'Prediction' column found)")
                continue

            file_stem = file_path.stem.lower()

            # Apply the formatting directly to the existing Prediction column
            if 'cti-mcq' in file_stem:
                df['Prediction'] = df['Prediction'].apply(format_mcq)
            elif 'cti-rcm' in file_stem:
                df['Prediction'] = df['Prediction'].apply(format_rcm)
            elif 'cti-vsp' in file_stem:
                df['Prediction'] = df['Prediction'].apply(format_vsp)
            elif 'cti-taa' in file_stem:
                df['Prediction'] = df['Prediction'].apply(format_taa)
            elif 'cti-ate' in file_stem:
                df['Prediction'] = df['Prediction'].apply(format_ate)

            # Save as standard .tsv using tab separator
            df.to_csv(out_path, index=False, sep='\t', encoding='utf-8')
            print("DONE")
            
        except Exception as e:
            print(f"FAILED ({e})")

    print("\nAll preprocessing complete. Check the 'PREPROCESSED_outputs' folder for your TSV files!")

if __name__ == "__main__":
    process_files()
