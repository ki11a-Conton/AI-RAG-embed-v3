import json
import os
import re

from dotenv import load_dotenv


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config() -> dict:
    load_dotenv(os.path.join(PROJECT_DIR, ".env"))

    config_path = os.path.join(PROJECT_DIR, "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(PROJECT_DIR, "config_example.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if "llm" in config:
        config["llm"]["api_key"] = os.getenv(
            "LLM_API_KEY", config["llm"].get("api_key", "")
        )
    if "enhancer" in config:
        config["enhancer"]["api_key"] = os.getenv(
            "ENHANCER_API_KEY", config["enhancer"].get("api_key", "")
        )
    if "image_caption" in config:
        config["image_caption"]["api_key"] = os.getenv(
            "IMAGE_CAPTION_API_KEY", config["image_caption"].get("api_key", "")
        )
    if "image_caption_api_key" in config:
        config["image_caption_api_key"] = os.getenv(
            "IMAGE_CAPTION_API_KEY", config.get("image_caption_api_key", "")
        )

    return config


def resolve_path(config: dict, key: str) -> str:
    path = config[key]
    if path.startswith("./") or path.startswith(".\\"):
        return os.path.join(PROJECT_DIR, path[2:])
    return path


# ── Knowledge-base name validation & overlay ──────────────────────────────


def validate_kb_name(name: str) -> str:
    """Validate *name* is a safe slug: letters, digits, underscore, hyphen, dot.

    Returns the validated name on success.
    Raises :exc:`ValueError` with a descriptive message on failure.
    """
    if not name or not isinstance(name, str):
        raise ValueError("Knowledge-base name must be a non-empty string.")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
        raise ValueError(
            f"Invalid knowledge-base name {name!r}. "
            "Only letters, digits, underscore, hyphen, and dot are allowed."
        )
    if ".." in name:
        raise ValueError(
            f"Knowledge-base name {name!r} contains '..' and is rejected as "
            "a path-traversal risk."
        )
    if name.startswith("."):
        raise ValueError(
            f"Knowledge-base name {name!r} starts with '.' and is rejected."
        )
    return name


def apply_kb_overlay(config: dict, kb_name: str) -> dict:
    """Return a new config dict with *docs_dir* and *chroma_persist_dir*
    overlaid to ``./knowledge_bases/<kb_name>/documents`` and
    ``./knowledge_bases/<kb_name>/chroma_db`` respectively.

    Raises :exc:`ValueError` when *kb_name* fails validation.
    """
    safe = validate_kb_name(kb_name)
    cfg = dict(config)
    kb_root = os.path.join(PROJECT_DIR, "knowledge_bases", safe)
    cfg["docs_dir"] = os.path.join(kb_root, "documents")
    cfg["chroma_persist_dir"] = os.path.join(kb_root, "chroma_db")
    return cfg
