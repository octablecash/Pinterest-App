"""Konfiguration aus Umgebungsvariablen bzw. lokaler .env-Datei.

Secrets (App Secret, Tokens) werden nie im Code oder Repo gespeichert.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"

load_dotenv(ENV_FILE)

API_BASE = os.getenv("PINTEREST_API_BASE", "https://api.pinterest.com/v5").rstrip("/")
AUTH_URL = "https://www.pinterest.com/oauth/"
SCOPES = ["boards:read", "pins:read", "pins:write"]


class ConfigError(RuntimeError):
    pass


def get(name, required=True):
    value = os.getenv(name, "").strip()
    if required and not value:
        raise ConfigError(
            f"{name} fehlt. Trage den Wert in die Datei .env ein (Vorlage: .env.example)."
        )
    return value


def save_env(updates):
    """Schreibt/aktualisiert Schlüssel in der lokalen .env, andere Zeilen bleiben erhalten."""
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    remaining = dict(updates)
    out = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in remaining and not line.lstrip().startswith("#"):
            out.append(f"{key}={remaining.pop(key)}")
        else:
            out.append(line)
    out.extend(f"{k}={v}" for k, v in remaining.items())
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    try:
        ENV_FILE.chmod(0o600)
    except OSError:
        pass  # z. B. unter Windows nicht relevant
    for k, v in updates.items():
        os.environ[k] = v
