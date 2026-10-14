import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Racine projet : src/assistant/utils -> parents[3]
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_env_file() -> None:
    candidates = [
        ROOT / ".env",
        Path.cwd() / ".env",
    ]
    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=True, encoding="utf-8")


def load_environment() -> Path:
    _load_env_file()

    try:
        for key in ("GROQ_API_KEY", "DATABASE_URL", "GROQ_MODEL", "MAX_RETRIES"):
            if key in st.secrets:
                value = str(st.secrets[key]).strip()
                if value:
                    os.environ[key] = value
    except Exception:
        pass

    return ROOT


def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()
