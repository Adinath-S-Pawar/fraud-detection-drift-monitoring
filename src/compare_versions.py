"""
Compare two trained model versions side by side, to inform a manual promote decision.

Run: python -m src.compare_versions v1 v2
"""

import json
import sys

from src import config


def load_metrics(version: str) -> dict:
    paths = config.get_versioned_paths(version)
    with open(paths["metrics"]) as f:
        return json.load(f)


def compare(version_a: str, version_b: str):
    metrics_a = load_metrics(version_a)
    metrics_b = load_metrics(version_b)

    print(f"{'Metric':<20}{version_a:>15}{version_b:>15}{'Change':>15}")
    print("-" * 65)

    for key in ["roc_auc", "pr_auc"]:
        a, b = metrics_a[key], metrics_b[key]
        change = b - a
        arrow = "up" if change > 0 else ("down" if change < 0 else "same")
        print(f"{key:<20}{a:>15.4f}{b:>15.4f}{change:>+15.4f}  ({arrow})")

    print()
    current_version_file = config.CURRENT_VERSION_FILE
    live_version = current_version_file.read_text().strip() if current_version_file.exists() else "none"
    print(f"Currently live version: {live_version}")

    if metrics_b["pr_auc"] > metrics_a["pr_auc"]:
        print(f"\n{version_b} has higher PR-AUC — candidate for promotion.")
    else:
        print(f"\n{version_b} does not improve PR-AUC over {version_a} — promotion not recommended.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m src.compare_versions <version_a> <version_b>")
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])