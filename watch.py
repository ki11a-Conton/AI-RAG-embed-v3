"""
watch.py
Watch the documents directory and trigger incremental indexing after changes.

Usage:
    python watch.py
    python watch.py --debounce 10
    python watch.py --kb project_a
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    FileSystemEventHandler = object  # type: ignore[assignment]
    Observer = None  # type: ignore[assignment]

from lib.config import apply_kb_overlay, load_config
from lib.doc_loader import SUPPORTED_EXTENSIONS


class _DebounceHandler(FileSystemEventHandler):
    """Coalesce short bursts of file events into one incremental build."""

    def __init__(self, config: dict, debounce_seconds: float = 5.0,
                 kb_name: str | None = None):
        super().__init__()
        self._config = config
        self._debounce = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._pending_paths: set[str] = set()
        self.kb_name = kb_name

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return

        ext = os.path.splitext(event.src_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return

        with self._lock:
            self._pending_paths.add(event.src_path)
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._trigger)
            self._timer.daemon = True
            self._timer.start()

    def _trigger(self) -> None:
        with self._lock:
            paths = set(self._pending_paths)
            self._pending_paths.clear()
            self._timer = None

        kb_label = f" (kb={self.kb_name})" if self.kb_name else ""
        print(f"\n[watch{kb_label}] Detected {len(paths)} changed file(s); running incremental build...")
        for path in sorted(paths):
            print(f"  - {path}")

        try:
            from rag_runner import cmd_build_incremental

            cmd_build_incremental(self._config)
            print(f"[watch{kb_label}] Incremental build complete.\n")
        except Exception as exc:
            print(f"[watch{kb_label}] Incremental build failed: {exc}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watch documents/ and trigger incremental indexing."
    )
    parser.add_argument(
        "--debounce",
        type=float,
        default=5.0,
        help="Debounce window in seconds. Default: 5.",
    )
    parser.add_argument(
        "--kb",
        type=str,
        default=None,
        help="Knowledge-base name to watch (knowledge_bases/<NAME>/documents).",
    )
    args = parser.parse_args()

    if Observer is None:
        print("[watch] Error: watchdog is not installed. Run: pip install watchdog")
        sys.exit(1)

    config = load_config()
    kb_name = args.kb
    if kb_name:
        try:
            config = apply_kb_overlay(config, kb_name)
        except ValueError as exc:
            print(f"[watch] Error: {exc}")
            sys.exit(1)

    docs_dir = config.get("docs_dir", "./documents")
    if not os.path.isdir(docs_dir):
        print(f"[watch] Error: documents directory does not exist: {docs_dir}")
        sys.exit(1)

    handler = _DebounceHandler(config, debounce_seconds=args.debounce,
                               kb_name=kb_name)
    observer = Observer()
    observer.schedule(handler, path=docs_dir, recursive=True)
    observer.start()

    kb_label = f" (kb={kb_name})" if kb_name else ""
    print(f"[watch{kb_label}] Watching: {os.path.abspath(docs_dir)}")
    print(f"[watch] Debounce window: {args.debounce}s | Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
            if not observer.is_alive():
                break
    except KeyboardInterrupt:
        print("\n[watch] Stopping")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
