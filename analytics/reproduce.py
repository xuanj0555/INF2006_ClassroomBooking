from pathlib import Path
import os
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIRECTORY = PROJECT_ROOT / "analytics" / "output"

EXPECTED_OUTPUTS = [
    OUTPUT_DIRECTORY / "reservations_by_room.csv",
    OUTPUT_DIRECTORY / "reservations_by_weekday.csv",
    OUTPUT_DIRECTORY / "reservations_by_start_hour.csv",
    OUTPUT_DIRECTORY / "summary_metrics.json",
]


def run(command):
    print(f"\nRunning: {' '.join(str(item) for item in command)}")

    environment = os.environ.copy()

    # Ensure the notebook kernel uses the same Python environment
    # that was used to launch this reproduction script.
    python_directory = str(Path(sys.executable).parent)
    environment["PATH"] = (
        python_directory
        + os.pathsep
        + environment.get("PATH", "")
    )

    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )


print("Starting Roomly analytics reproduction")

run([
    sys.executable,
    str(PROJECT_ROOT / "data" / "prepare_reservations.py"),
])

run([
    sys.executable,
    "-m",
    "jupyter",
    "nbconvert",
    "--to",
    "notebook",
    "--execute",
    str(PROJECT_ROOT / "analytics" / "reservation_analysis.ipynb"),
    "--inplace",
    "--ExecutePreprocessor.timeout=600",
])

missing_outputs = [
    path for path in EXPECTED_OUTPUTS
    if not path.exists()
]

if missing_outputs:
    print("\nERROR: The following output files were not produced:")
    for path in missing_outputs:
        print(f"- {path}")
    raise SystemExit(1)

print("\nPASS: analytics reproduced successfully")
print(f"Output location: {OUTPUT_DIRECTORY}")