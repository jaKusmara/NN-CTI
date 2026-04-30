import pandas as pd
import re
import os
import pickle
from pathlib import Path
from cvss import CVSS3  # Required for VSP evaluation

# ==========================================
# 1. Metric Calculators
# ==========================================

def compute_mcq_accuracy(fname, col):
    df = pd.read_csv(fname, sep='\t')
    correct = 0
    total = 0
    for idx, row in df.iterrows():
        pred = str(row[col]).strip().upper()
        gt = str(row['GT']).strip().upper()
        if pred in ['A', 'B', 'C', 'D', 'X']:
            total += 1
        if pred == gt:
            correct += 1
    return (correct / total * 100) if total > 0 else 0


def compute_rcm_accuracy(fname, col):
    df = pd.read_csv(fname, sep='\t')
    correct = 0
    total = 0
    for idx, row in df.iterrows():
        pred = str(row[col]).strip().upper()
        gt = str(row['GT']).strip().upper()
        if pred.startswith('CWE-'):
            total += 1
        if pred == gt:
            correct += 1
    return (correct / total * 100) if total > 0 else 0


def get_cvss_score(cvss_vector):
    # Some models might accidentally append the prefix, so we strip and rebuild cleanly
    vector_string = cvss_vector.replace("CVSS:3.0/", "").replace("CVSS:3.1/", "")
    clean_vector = "CVSS:3.1/" + vector_string
    c = CVSS3(clean_vector)
    return c.scores()[0]

def compute_vsp_mad(fname, col):
    df = pd.read_csv(fname, sep='\t')
    error = 0
    total = 0
    for idx, row in df.iterrows():
        pred = str(row[col]).strip().upper()
        gt = str(row['GT']).strip().upper()
        try:
            pred_score = get_cvss_score(pred)
            gt_score = get_cvss_score(gt)
            error += abs(pred_score - gt_score)
            total += 1
        except Exception:
            continue
            
    return (error / total) if total > 0 else 0


def compute_ate_metrics(fname, col):
    """Calculates Exact Match, Precision, Recall, and F1 for multiple MITRE IDs"""
    df = pd.read_csv(fname, sep='\t')
    exact_matches = 0
    total_p, total_r, total_f1 = 0, 0, 0
    total = len(df)
    
    if total == 0: return 0, 0, 0, 0
    
    for idx, row in df.iterrows():
        pred = str(row[col])
        gt = str(row['GT'])
        
        pred_set = set(re.findall(r'T\d{4}', pred))
        gt_set = set(re.findall(r'T\d{4}', gt))
        
        if pred_set == gt_set:
            exact_matches += 1
            
        tp = len(pred_set & gt_set)
        fp = len(pred_set - gt_set)
        fn = len(gt_set - pred_set)
        
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        
        total_p += p
        total_r += r
        total_f1 += f1
        
    return (exact_matches/total*100), (total_p/total*100), (total_r/total*100), (total_f1/total*100)


# ==========================================
# 2. Main Runner
# ==========================================

BASE_DIR = Path("PREPROCESSED_outputs")

def run_evaluation():
    if not BASE_DIR.exists():
        print(f"Directory {BASE_DIR} not found. Did you run the preprocessor script?")
        return

    # Find all model folders inside PREPROCESSED_outputs
    model_folders = [f for f in BASE_DIR.iterdir() if f.is_dir()]
    
    if not model_folders:
        print("No model folders found to evaluate.")
        return

    print("="*50)
    print(" CTI BENCHMARK EVALUATION RESULTS")
    print("="*50)

    # Evaluate each model dynamically
    for model_dir in model_folders:
        model_name = model_dir.name
        print(f"\nEvaluating Model: {model_name}")
        print("-" * 30)
        
        # Define expected paths
        mcq_file = model_dir / "cti-mcq-res.tsv"
        rcm_file = model_dir / "cti-rcm-res.tsv"
        rcm_2021_file = model_dir / "cti-rcm-2021-res.tsv"
        vsp_file = model_dir / "cti-vsp-res.tsv"
        ate_file = model_dir / "cti-ate-res.tsv"
        
        # 1. Evaluate MCQ
        if mcq_file.exists():
            score = compute_mcq_accuracy(mcq_file, 'Prediction')
            print(f"  [MCQ] Accuracy:       {score:.2f}%")
            
        # 2. Evaluate RCM
        if rcm_file.exists():
            score = compute_rcm_accuracy(rcm_file, 'Prediction')
            print(f"  [RCM] Accuracy:       {score:.2f}%")
            
        # 3. Evaluate RCM-2021
        if rcm_2021_file.exists():
            score = compute_rcm_accuracy(rcm_2021_file, 'Prediction')
            print(f"  [RCM 2021] Accuracy:  {score:.2f}%")
            
        # 4. Evaluate VSP
        if vsp_file.exists():
            score = compute_vsp_mad(vsp_file, 'Prediction')
            print(f"  [VSP] Mean Abs Dev:   {score:.4f} (Lower is better)")
            
        # 5. Evaluate ATE
        if ate_file.exists():
            exact, p, r, f1 = compute_ate_metrics(ate_file, 'Prediction')
            print(f"  [ATE] Exact Match:    {exact:.2f}%")
            print(f"  [ATE] Macro F1 Score: {f1:.2f}%")

if __name__ == "__main__":
    run_evaluation()
