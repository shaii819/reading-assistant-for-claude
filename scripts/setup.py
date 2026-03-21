#!/usr/bin/env python3
"""Set up reading-assistant venv and install dependencies."""

import subprocess
import sys
import os
from pathlib import Path

VENV_DIR = Path.home() / ".reading-assistant" / "venv"
PLUGIN_ROOT = Path(__file__).parent.parent
REQUIREMENTS = PLUGIN_ROOT / "requirements.txt"


def main():
    print(f"Creating venv at {VENV_DIR}...")
    VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)

    pip = VENV_DIR / "bin" / "pip"
    print("Installing dependencies...")
    subprocess.run([str(pip), "install", "-r", str(REQUIREMENTS)], check=True)

    python = VENV_DIR / "bin" / "python"
    print("Validating imports...")
    for module in ["ebooklib", "sqlite_vec", "langdetect", "tiktoken", "bs4"]:
        result = subprocess.run(
            [str(python), "-c", f"import {module}; print('{module} OK')"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"FAIL: {module} — {result.stderr.strip()}")
            sys.exit(1)
        print(f"  {result.stdout.strip()}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        print("  OPENAI_API_KEY: set")
    else:
        print("  OPENAI_API_KEY: not set (embedding/external models will use Ollama)")

    hc_key = os.environ.get("HARDCOVER_API_KEY")
    if hc_key:
        print("  HARDCOVER_API_KEY: set")
    else:
        print("  HARDCOVER_API_KEY: not set (Hardcover reviews will be skipped)")

    print("\nSetup complete.")


if __name__ == "__main__":
    main()
