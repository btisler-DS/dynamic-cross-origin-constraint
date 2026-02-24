"""Thin wrapper to run Protocol 1 (Interrogative Emergence).

Usage:
    python run_inquiry.py --epochs 500 --episodes 10 --seed 42
"""

import subprocess
import sys

if __name__ == "__main__":
    subprocess.run(
        [sys.executable, "-m", "simulation.engine", "--protocol", "1", *sys.argv[1:]],
        check=True,
    )
