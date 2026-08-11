#!/usr/bin/env python
import argparse
import os
import subprocess
import sys
from pathlib import Path


def load_env_file(env_path: Path) -> None:
    """Helper to parse key-value pairs from a .env file into os.environ if not already set."""
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val


def main():
    """
    Dynamically installs dependencies based on CLASSIFICATION_MODEL / EMAIL_CLASSIFIER_MODEL / CLASSIFIER_MODE.
    Reads settings directly from ml-service/.env or system environment variables.
    """
    parser = argparse.ArgumentParser(description="Dynamic ML Service Dependency Installer")
    parser.add_argument("--uv", action="store_true", help="Use Astral uv package manager for installation")
    parser.add_argument("--cpu", action="store_true", help="Use CPU PyTorch index when installing PyTorch")
    args = parser.parse_args()

    # Load ml-service/.env file if present
    script_dir = Path(__file__).parent.resolve()
    load_env_file(script_dir / ".env")

    # Determine classification model dynamically from environment variables or .env
    model_name = (
        os.getenv("CLASSIFICATION_MODEL")
        or os.getenv("EMAIL_CLASSIFIER_MODEL")
        or os.getenv("CLASSIFIER_MODE")
        or "mlops"
    ).lower()

    install_heavy = os.getenv("INSTALL_HEAVY_ML", "false").lower() in ("true", "1", "yes")

    # Lightweight modes: mlops, linear_svc, light
    is_light_mode = model_name in ("mlops", "linear_svc", "light") and not install_heavy

    if is_light_mode:
        print(f"📦 [ML Service] Detected CLASSIFICATION_MODEL='{model_name}'")
        print("🚀 [ML Service] Installing Lightweight Dependencies (Skipping PyTorch/Transformers)...")
        req_file = "requirements-base.txt"
    else:
        print(f"📦 [ML Service] Detected CLASSIFICATION_MODEL='{model_name}'")
        print("🔥 [ML Service] Installing Full Deep Learning Dependencies (PyTorch & Transformers)...")
        req_file = "requirements.txt"

    if args.uv:
        cmd = ["uv", "pip", "install", "--system"]
        if not is_light_mode and args.cpu:
            cmd.extend(["--index-strategy", "unsafe-best-match", "--extra-index-url", "https://download.pytorch.org/whl/cpu"])
        cmd.extend(["-r", req_file])
    else:
        cmd = [sys.executable, "-m", "pip", "install"]
        if not is_light_mode and args.cpu:
            cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/cpu"])
        cmd.extend(["-r", req_file])

    print(f"Executing command: {' '.join(cmd)}")
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
