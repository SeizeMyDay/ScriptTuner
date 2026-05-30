from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
REQUIREMENTS = ROOT_DIR / "requirements.txt"
INSTALL_STAMP = VENV_DIR / ".script_tuner_installed"


def run(command: list[str]) -> None:
    print(f"> {' '.join(command)}", flush=True)
    subprocess.check_call(command, cwd=ROOT_DIR)


def ensure_supported_python() -> None:
    if sys.version_info < (3, 11):
        raise SystemExit(
            "Script-Tuner requires Python 3.11 or newer. "
            f"Current Python is {sys.version.split()[0]}."
        )


def ensure_venv() -> None:
    if VENV_PYTHON.exists():
        return
    print("Creating local virtual environment in .venv...", flush=True)
    run([sys.executable, "-m", "venv", str(VENV_DIR)])


def ensure_dependencies() -> None:
    if INSTALL_STAMP.exists():
        return
    print("Installing Script-Tuner dependencies. This can take several minutes on first run.", flush=True)
    run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    INSTALL_STAMP.write_text("ok\n", encoding="utf-8")


def run_service() -> int:
    env = os.environ.copy()
    return subprocess.call([str(VENV_PYTHON), str(ROOT_DIR / "run_app.py")], cwd=ROOT_DIR, env=env)


def main() -> None:
    ensure_supported_python()
    ensure_venv()
    ensure_dependencies()
    raise SystemExit(run_service())


if __name__ == "__main__":
    main()
