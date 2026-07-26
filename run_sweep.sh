#!/bin/bash
# Sweep script: runs X86O3CPU across ROB sizes and issue widths
# Usage: ./run_sweep.sh <workload_binary> <workload_name>
# Example: ./run_sweep.sh test.bin baseline

WORKLOAD_BIN=$1
WORKLOAD_NAME=$2

if [ -z "$WORKLOAD_BIN" ] || [ -z "$WORKLOAD_NAME" ]; then
    echo "Usage: ./run_sweep.sh <workload_binary> <workload_name>"
    exit 1
fi

ROB_SIZES=(32 64 128 192)
ISSUE_WIDTHS=(1 2 4)

for rob in "${ROB_SIZES[@]}"; do
    for iw in "${ISSUE_WIDTHS[@]}"; do
        OUTDIR="results/${WORKLOAD_NAME}_rob${rob}_iw${iw}"
        echo ">>> Running ${WORKLOAD_NAME}: ROB=${rob}, issue_width=${iw}"
        ./build/X86/gem5.opt --outdir="${OUTDIR}" rob_iw_config.py \
            --cmd="${WORKLOAD_BIN}" --rob-size="${rob}" --issue-width="${iw}" \
            > "${OUTDIR}_log.txt" 2>&1

        # Extract IPC immediately for a quick running summary
        IPC=$(grep "system.cpu.ipc" "${OUTDIR}/stats.txt" | head -1 | awk '{print $2}')
        echo "    IPC = ${IPC}"
        echo "${WORKLOAD_NAME},${rob},${iw},${IPC}" >> sweep_results.csv
    done
done

echo ""
echo "Sweep complete. Results appended to sweep_results.csv"
