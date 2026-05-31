"""Knowledge-base discovery helpers."""
import os

from lib.config import PROJECT_DIR, apply_kb_overlay, validate_kb_name


def list_knowledge_bases() -> list[str]:
    """Return available knowledge-base names.

    The default config-backed knowledge base is always present. Extra entries
    are discovered from ``knowledge_bases/<name>/chroma_db`` directories.
    """
    names = ["default"]
    kb_root = os.path.join(PROJECT_DIR, "knowledge_bases")
    if not os.path.isdir(kb_root):
        return names

    for entry in sorted(os.scandir(kb_root), key=lambda item: item.name):
        if not entry.is_dir():
            continue
        try:
            validate_kb_name(entry.name)
        except ValueError:
            continue
        chroma_path = os.path.join(entry.path, "chroma_db")
        if os.path.isdir(chroma_path):
            names.append(entry.name)
    return names


def kb_config(base_config: dict, kb_name: str) -> dict:
    """Return the effective config for *kb_name*."""
    if kb_name == "default":
        return base_config
    return apply_kb_overlay(base_config, kb_name)
