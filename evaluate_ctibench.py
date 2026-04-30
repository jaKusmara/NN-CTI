import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
from cvss import CVSS3


TASK_FILES = {
    "MCQ": "cti-mcq-responses.tsv",
    "RCM": "cti-rcm-responses.tsv",
    "RCM 2021": "cti-rcm-2021-responses.tsv",
    "VSP": "cti-vsp-responses.tsv",
}


RESULT_COLUMNS = [
    "model",
    "MCQ Accuracy",
    "RCM Accuracy",
    "RCM 2021 Accuracy",
    "VSP Mean Abs Dev",
]


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def load_tsv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        print(f"[WARN] Missing file: {path}")
        return None
    return pd.read_csv(path, sep="\t")


def response_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c != "GT"]


def compute_mcq_accuracy(df: pd.DataFrame, col: str) -> float | None:
    correct = 0
    total = 0

    for _, row in df.iterrows():
        pred = safe_str(row.get(col)).upper()
        gt = safe_str(row.get("GT")).upper()

        if pred in {"A", "B", "C", "D", "X"}:
            total += 1
            if pred == gt:
                correct += 1

    return None if total == 0 else correct / total * 100


def compute_rcm_accuracy(df: pd.DataFrame, col: str) -> float | None:
    correct = 0
    total = 0

    for _, row in df.iterrows():
        pred = safe_str(row.get(col)).upper()
        gt = safe_str(row.get("GT")).upper()

        if pred.startswith("CWE-"):
            total += 1
            if pred == gt:
                correct += 1

    return None if total == 0 else correct / total * 100


def cvss_score(vector: str) -> float:
    return CVSS3(vector).scores()[0]


def normalize_cvss_vector(value: Any) -> str:
    value = safe_str(value).upper()
    if value.startswith("CVSS:3."):
        return value
    return "CVSS:3.0/" + value


def compute_vsp_mad(df: pd.DataFrame, col: str) -> float | None:
    error = 0.0
    total = 0

    for _, row in df.iterrows():
        pred = normalize_cvss_vector(row.get(col))
        gt = safe_str(row.get("GT")).upper()

        try:
            error += abs(cvss_score(pred) - cvss_score(gt))
            total += 1
        except Exception:
            continue

    return None if total == 0 else error / total


def fmt_percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}%"


def fmt_float(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".", help="Path to cloned cti-bench repository")
    parser.add_argument("--out", default="ctibench_output_results", help="Output directory")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    eval_dir = repo / "evaluation"
    responses_dir = eval_dir / "responses"
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not responses_dir.exists():
        raise FileNotFoundError(f"Responses directory not found: {responses_dir}")

    dfs = {task: load_tsv(responses_dir / fname) for task, fname in TASK_FILES.items()}

    all_models: set[str] = set()
    for df in dfs.values():
        if df is not None:
            all_models.update(response_columns(df))

    rows: list[dict[str, Any]] = []

    for model in sorted(all_models):
        row: dict[str, Any] = {"model": model}

        if dfs["MCQ"] is not None and model in dfs["MCQ"].columns:
            row["MCQ Accuracy"] = compute_mcq_accuracy(dfs["MCQ"], model)
        else:
            row["MCQ Accuracy"] = None

        if dfs["RCM"] is not None and model in dfs["RCM"].columns:
            row["RCM Accuracy"] = compute_rcm_accuracy(dfs["RCM"], model)
        else:
            row["RCM Accuracy"] = None

        if dfs["RCM 2021"] is not None and model in dfs["RCM 2021"].columns:
            row["RCM 2021 Accuracy"] = compute_rcm_accuracy(dfs["RCM 2021"], model)
        else:
            row["RCM 2021 Accuracy"] = None

        if dfs["VSP"] is not None and model in dfs["VSP"].columns:
            row["VSP Mean Abs Dev"] = compute_vsp_mad(dfs["VSP"], model)
        else:
            row["VSP Mean Abs Dev"] = None

        rows.append(row)

    result_df = pd.DataFrame(rows, columns=RESULT_COLUMNS)

    result_df.to_csv(out_dir / "ctibench_repo_results.csv", index=False)

    with (out_dir / "ctibench_repo_results.json").open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    txt_lines: list[str] = []
    txt_lines.append("=" * 50)
    txt_lines.append(" CTI BENCHMARK EVALUATION RESULTS")
    txt_lines.append("=" * 50)
    txt_lines.append("")

    for row in rows:
        txt_lines.append(f"Evaluating Model: {row['model']}")
        txt_lines.append("-" * 30)
        txt_lines.append(f"  [MCQ] Accuracy:       {fmt_percent(row['MCQ Accuracy'])}")
        txt_lines.append(f"  [RCM] Accuracy:       {fmt_percent(row['RCM Accuracy'])}")
        txt_lines.append(f"  [RCM 2021] Accuracy:  {fmt_percent(row['RCM 2021 Accuracy'])}")
        txt_lines.append(f"  [VSP] Mean Abs Dev:   {fmt_float(row['VSP Mean Abs Dev'])} (Lower is better)")
        txt_lines.append("")

    (out_dir / "ctibench_repo_results.txt").write_text("\n".join(txt_lines), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append("# CTI-Bench Repository Results")
    md_lines.append("")
    md_lines.append("| Model | MCQ Acc. | RCM Acc. | RCM 2021 Acc. | VSP MAD ↓ |")
    md_lines.append("|---|---:|---:|---:|---:|")

    for row in rows:
        md_lines.append(
            f"| {row['model']} | "
            f"{fmt_percent(row['MCQ Accuracy'])} | "
            f"{fmt_percent(row['RCM Accuracy'])} | "
            f"{fmt_percent(row['RCM 2021 Accuracy'])} | "
            f"{fmt_float(row['VSP Mean Abs Dev'])} |"
        )

    md_lines.append("")
    md_lines.append("> Poznámka: TAA je úplne odstránené. Skript nečíta `cti-taa-responses.tsv`, `alias_dict.pickle` ani `related_dict.pickle`.")

    (out_dir / "ctibench_repo_results.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Done. Results written to: {out_dir}")
    print(f"- {out_dir / 'ctibench_repo_results.csv'}")
    print(f"- {out_dir / 'ctibench_repo_results.txt'}")
    print(f"- {out_dir / 'ctibench_repo_results.md'}")
    print(f"- {out_dir / 'ctibench_repo_results.json'}")


if __name__ == "__main__":
    main()
