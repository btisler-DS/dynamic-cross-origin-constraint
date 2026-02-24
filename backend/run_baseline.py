"""Thin wrapper to run Protocol 0 (Baseline — replicates Run 10 behaviour).

Usage:
    python run_baseline.py --epochs 100 --episodes 10 --seed 42
"""

import subprocess
import sys

if __name__ == "__main__":
    subprocess.run(
        [sys.executable, "-m", "simulation.engine", "--protocol", "0", *sys.argv[1:]],
        check=True,
    )
