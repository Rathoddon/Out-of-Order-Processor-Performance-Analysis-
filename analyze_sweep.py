"""
analyze_sweep.py
Run this from your ~/gem5/ folder after your sweep is complete.

Usage:
    python3 analyze_sweep.py

Requires: pandas, matplotlib  (install with: pip3 install pandas matplotlib)

What it does:
1. Reads sweep_results.csv -> plots IPC vs ROB size (one line per issue width),
   one subplot per workload.
2. Scans each results/<workload>_rob<X>_iw<Y>/stats.txt for bottleneck-related
   stats (fetch stalls, ROB-full events, branch mispredicts, memory stalls)
   and builds a summary CSV + printed table.
"""

import os
import re
import csv
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
SWEEP_CSV = "sweep_results.csv"
BOTTLENECK_CSV = "bottleneck_summary.csv"

# ---------- PART 1: IPC vs ROB plots ----------

def plot_ipc_curves():
    df = pd.read_csv(SWEEP_CSV)
    df["ipc"] = pd.to_numeric(df["ipc"], errors="coerce")

    workloads = df["workload"].unique()
    fig, axes = plt.subplots(1, len(workloads), figsize=(6 * len(workloads), 5), sharey=True)
    if len(workloads) == 1:
        axes = [axes]

    for ax, wl in zip(axes, workloads):
        sub = df[df["workload"] == wl]
        for iw in sorted(sub["issue_width"].unique()):
            line = sub[sub["issue_width"] == iw].sort_values("rob")
            ax.plot(line["rob"], line["ipc"], marker="o", label=f"issue_width={iw}")
        ax.set_title(wl)
        ax.set_xlabel("ROB size")
        ax.set_ylabel("IPC")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("ipc_vs_rob.png", dpi=150)
    print("Saved plot: ipc_vs_rob.png")


# ---------- PART 2: Bottleneck stat extraction ----------

# Patterns to try for each metric (gem5 stat names vary by version).
# The script tries each pattern in order and uses the first match found.
PATTERNS = {
    "rob_full_events": [
        r"system\.cpu\.rename\.ROBFullEvents\s+(\S+)",
    ],
    "icache_stall_cycles": [
        r"system\.cpu\.fetchStats0\.icacheStallCycles\s+(\S+)",
    ],
    "fetch_misc_stall_cycles": [
        r"system\.cpu\.fetch\.miscStallCycles\s+(\S+)",
    ],
    "branch_squashes": [
        r"system\.cpu\.branchPred\.squashes_0::total\s+(\S+)",
    ],
    "mem_order_violations": [
        r"system\.cpu\.iew\.memOrderViolationEvents\s+(\S+)",
    ],
    "num_cycles": [
        r"system\.cpu\.numCycles\s+(\S+)",
    ],
    "ipc": [
        r"system\.cpu\.ipc\s+(\S+)",
    ],
}


def extract_stat(text, keys):
    for pattern in keys:
        m = re.search(pattern, text)
        if m:
            raw = m.group(1).replace(",", "").rstrip("%")
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def bottleneck_scan():
    rows = []
    if not os.path.isdir(RESULTS_DIR):
        print(f"No '{RESULTS_DIR}' directory found — run this from your ~/gem5 folder.")
        return

    for entry in sorted(os.listdir(RESULTS_DIR)):
        stats_path = os.path.join(RESULTS_DIR, entry, "stats.txt")
        if not os.path.isfile(stats_path):
            continue

        # Parse workload/rob/iw from folder name: e.g. memory_rob64_iw2
        m = re.match(r"(\w+?)_rob(\d+)_iw(\d+)", entry)
        if not m:
            continue
        workload, rob, iw = m.group(1), int(m.group(2)), int(m.group(3))

        with open(stats_path, "r", errors="ignore") as f:
            text = f.read()

        row = {"workload": workload, "rob": rob, "issue_width": iw}
        for metric, patterns in PATTERNS.items():
            row[metric] = extract_stat(text, patterns)
        rows.append(row)

    if not rows:
        print("No matching result folders found under results/.")
        return

    with open(BOTTLENECK_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved bottleneck summary: {BOTTLENECK_CSV}")
    df = pd.DataFrame(rows)
    print("\n--- Bottleneck summary (first 15 rows) ---")
    print(df.head(15).to_string(index=False))

    # Flag which metrics came back empty across the board (stat name mismatch)
    for metric in PATTERNS:
        if metric == "ipc":
            continue
        if df[metric].isna().all():
            print(f"\n[!] '{metric}' was not found under any tried pattern.")
            print("    Run the grep command from the instructions to find the correct stat name,")
            print("    then add it to PATTERNS in this script.")


if __name__ == "__main__":
    plot_ipc_curves()
    bottleneck_scan()
