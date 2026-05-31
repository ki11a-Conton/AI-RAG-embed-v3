#!/usr/bin/env python3
"""
init_project.py

First-run setup helper for AI-RAG-embed.
It creates local config files and required runtime directories without
overwriting existing user files.
"""
import os
import shutil
import sys

from dotenv import load_dotenv


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


def check(msg: str) -> None:
    print(f"{GREEN}[OK]{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def error(msg: str) -> None:
    print(f"{RED}[ERROR]{RESET} {msg}")


def step_check_python() -> None:
    if sys.version_info < (3, 10):
        error(f"Python 3.10+ is required. Current version: {sys.version}")
        sys.exit(1)
    check(f"Python version: {sys.version.split()[0]}")


def step_copy_config() -> None:
    config_path = os.path.join(PROJECT_DIR, "config.json")
    example_path = os.path.join(PROJECT_DIR, "config_example.json")
    if os.path.exists(config_path):
        check("config.json already exists; skipping copy")
        return
    shutil.copy2(example_path, config_path)
    check("Created config.json from config_example.json")


def step_copy_env() -> None:
    env_path = os.path.join(PROJECT_DIR, ".env")
    example_path = os.path.join(PROJECT_DIR, ".env.example")
    if os.path.exists(env_path):
        check(".env already exists; skipping copy")
        return
    shutil.copy2(example_path, env_path)
    warn("Created .env from .env.example. Edit .env and set:")
    warn("  LLM_API_KEY=your LLM API key")
    warn("  ENHANCER_API_KEY=optional query-enhancement API key")


def step_create_dirs() -> None:
    for dirname in ["documents", "logs", "knowledge_bases"]:
        os.makedirs(os.path.join(PROJECT_DIR, dirname), exist_ok=True)
    check("Required directories exist: documents/, logs/, knowledge_bases/")


def step_check_api_key() -> None:
    env_path = os.path.join(PROJECT_DIR, ".env")
    load_dotenv(env_path, override=True)
    llm_key = os.getenv("LLM_API_KEY", "").strip()
    if not llm_key or llm_key == "your-llm-api-key":
        warn("LLM_API_KEY is not configured. Edit .env before asking questions with the LLM.")
        return
    check("LLM_API_KEY is configured")


def step_print_next() -> None:
    print()
    print("=" * 50)
    print("Initialization complete. Next steps:")
    print()
    print("  1. Put your documents in documents/")
    print("     Supported: .txt .md .pdf .docx .pptx .html .csv .xlsx")
    print()
    print("  2. Build the index:")
    print("     python rag_runner.py --build")
    print()
    print("  3. Start a service:")
    print("     streamlit run app.py          # Web UI")
    print("     uvicorn api:app --port 8000   # REST API")
    print()
    print("  4. Ask from the command line:")
    print("     python rag_runner.py          # interactive chat")
    print("     python rag_runner.py \"question\" # one-shot question")
    print("=" * 50)


def main() -> None:
    print("AI-RAG-embed initialization")
    print("-" * 50)
    step_check_python()
    step_copy_config()
    step_copy_env()
    step_create_dirs()
    step_check_api_key()
    step_print_next()


if __name__ == "__main__":
    main()
