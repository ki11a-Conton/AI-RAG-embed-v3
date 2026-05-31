"""Tests for CLI override parsing in rag_runner._parse_cli_overrides."""

import sys

import pytest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run(argv, config=None):
    """Call ``_parse_cli_overrides`` with *argv* and return the updated config.

    Saves and restores ``sys.argv`` around the call.
    """
    saved = sys.argv[:]
    try:
        sys.argv = argv[:]
        cfg = {} if config is None else dict(config)
        from rag_runner import _parse_cli_overrides

        _parse_cli_overrides(cfg)
        return cfg, list(sys.argv)
    finally:
        sys.argv = saved


# ---------------------------------------------------------------------------
# --retrieval-k / --retrieval_k
# ---------------------------------------------------------------------------

class TestRetrievalK:
    def test_dash_form_sets_config_and_removes_args(self):
        """``--retrieval-k 10`` sets ``config['retrieval_k'] = 10`` and is removed."""
        cfg, argv = _run(["rag_runner.py", "--retrieval-k", "10", "my question"])
        assert cfg["retrieval_k"] == 10
        assert argv[1:] == ["my question"]

    def test_underscore_form_sets_config_and_removes_args(self):
        """``--retrieval_k 7`` sets ``config['retrieval_k'] = 7`` and is removed."""
        cfg, argv = _run(["rag_runner.py", "--retrieval_k", "7", "query"])
        assert cfg["retrieval_k"] == 7
        assert argv[1:] == ["query"]

    def test_before_command_flag(self):
        """Flag works before ``--retrieve``."""
        cfg, argv = _run(["rag_runner.py", "--retrieval-k", "3", "--retrieve", "question"])
        assert cfg["retrieval_k"] == 3
        assert argv[1:] == ["--retrieve", "question"]

    def test_after_command_flag(self):
        """Flag works after the question string."""
        cfg, argv = _run(["rag_runner.py", "--retrieve", "question", "--retrieval-k", "5"])
        assert cfg["retrieval_k"] == 5
        assert argv[1:] == ["--retrieve", "question"]

    def test_missing_value_exits(self):
        """Missing value after flag prints error and exits."""
        with pytest.raises(SystemExit):
            _run(["rag_runner.py", "--retrieval-k"])

    def test_non_integer_value_exits(self):
        """Non-integer value prints error and exits."""
        with pytest.raises(SystemExit):
            _run(["rag_runner.py", "--retrieval-k", "abc"])

    def test_zero_value_exits(self):
        """Zero is not a positive integer; exits with error."""
        with pytest.raises(SystemExit):
            _run(["rag_runner.py", "--retrieval-k", "0"])

    def test_negative_value_exits(self):
        """Negative integer is not positive; exits with error."""
        with pytest.raises(SystemExit):
            _run(["rag_runner.py", "--retrieval-k", "-1"])

    def test_overrides_existing_config_value(self):
        """Flag overrides a pre-existing config value."""
        cfg, _ = _run(
            ["rag_runner.py", "--retrieval-k", "20", "ask"],
            config={"retrieval_k": 5},
        )
        assert cfg["retrieval_k"] == 20


# ---------------------------------------------------------------------------
# --max-context-chars / --max_context_chars
# ---------------------------------------------------------------------------

class TestMaxContextChars:
    def test_dash_form_sets_config_and_removes_args(self):
        """``--max-context-chars 3000`` sets ``config['max_context_chars'] = 3000``."""
        cfg, argv = _run(["rag_runner.py", "--max-context-chars", "3000", "q"])
        assert cfg["max_context_chars"] == 3000
        assert argv[1:] == ["q"]

    def test_underscore_form_sets_config(self):
        """``--max_context_chars 4000`` sets ``config['max_context_chars'] = 4000``."""
        cfg, argv = _run(["rag_runner.py", "--max_context_chars", "4000", "q"])
        assert cfg["max_context_chars"] == 4000
        assert argv[1:] == ["q"]

    def test_missing_value_exits(self):
        with pytest.raises(SystemExit):
            _run(["rag_runner.py", "--max-context-chars"])

    def test_non_integer_exits(self):
        with pytest.raises(SystemExit):
            _run(["rag_runner.py", "--max-context-chars", "NaN"])

    def test_zero_exits(self):
        with pytest.raises(SystemExit):
            _run(["rag_runner.py", "--max-context-chars", "0"])

    def test_negative_exits(self):
        with pytest.raises(SystemExit):
            _run(["rag_runner.py", "--max-context-chars", "-100"])

    def test_overrides_existing_config_value(self):
        cfg, _ = _run(
            ["rag_runner.py", "--max-context-chars", "5000"],
            config={"max_context_chars": 6000},
        )
        assert cfg["max_context_chars"] == 5000


# ---------------------------------------------------------------------------
# --strict-context / --no-strict-context
# ---------------------------------------------------------------------------

class TestStrictContext:
    def test_strict_context_dash(self):
        """``--strict-context`` sets ``config['strict_context'] = True``."""
        cfg, argv = _run(["rag_runner.py", "--strict-context", "ask"])
        assert cfg["strict_context"] is True
        assert argv[1:] == ["ask"]

    def test_strict_context_underscore(self):
        """``--strict_context`` sets ``config['strict_context'] = True``."""
        cfg, argv = _run(["rag_runner.py", "--strict_context", "ask"])
        assert cfg["strict_context"] is True
        assert argv[1:] == ["ask"]

    def test_no_strict_context_dash(self):
        """``--no-strict-context`` sets ``config['strict_context'] = False``."""
        cfg, argv = _run(
            ["rag_runner.py", "--no-strict-context", "ask"],
            config={"strict_context": True},
        )
        assert cfg["strict_context"] is False
        assert argv[1:] == ["ask"]

    def test_no_strict_context_underscore(self):
        """``--no_strict_context`` sets ``config['strict_context'] = False``."""
        cfg, argv = _run(
            ["rag_runner.py", "--no_strict_context", "ask"],
            config={"strict_context": True},
        )
        assert cfg["strict_context"] is False
        assert argv[1:] == ["ask"]

    def test_toggle_from_strict_to_non_strict(self):
        """Using both flags: later flag wins."""
        cfg, argv = _run(
            ["rag_runner.py", "--strict-context", "--no-strict-context", "ask"],
        )
        assert cfg["strict_context"] is False
        assert argv[1:] == ["ask"]

    def test_toggle_from_non_strict_to_strict(self):
        """Using both flags: later flag wins."""
        cfg, _ = _run(
            ["rag_runner.py", "--no-strict-context", "--strict-context", "ask"],
        )
        assert cfg["strict_context"] is True


# ---------------------------------------------------------------------------
# Combination tests
# ---------------------------------------------------------------------------

class TestCombinations:
    def test_multiple_overrides(self):
        """Multiple overrides are all parsed and removed."""
        cfg, argv = _run([
            "rag_runner.py",
            "--retrieval-k", "15",
            "--max-context-chars", "2000",
            "--strict-context",
            "--retrieve", "my question",
        ])
        assert cfg["retrieval_k"] == 15
        assert cfg["max_context_chars"] == 2000
        assert cfg["strict_context"] is True
        assert argv[1:] == ["--retrieve", "my question"]

    def test_with_kb_flag(self):
        """Overrides work alongside ``--kb`` (order before ``--kb``)."""
        cfg, argv = _run([
            "rag_runner.py",
            "--retrieval-k", "8",
            "--kb", "mykb",
            "question?",
        ])
        assert cfg["retrieval_k"] == 8
        # --kb and its value are *not* consumed by _parse_cli_overrides
        # (model-agnostic: they remain in argv for subsequent parsing)
        assert argv[1:] == ["--kb", "mykb", "question?"]

    def test_unknown_flag_preserved(self):
        """Unknown flags are left untouched in argv."""
        cfg, argv = _run([
            "rag_runner.py",
            "--unknown-flag",
            "--retrieval-k", "5",
            "ask",
        ])
        assert cfg["retrieval_k"] == 5
        assert argv[1:] == ["--unknown-flag", "ask"]

    def test_no_overrides_preserves_all_args(self):
        """When no overrides are present, argv is unchanged."""
        cfg, argv = _run(["rag_runner.py", "--retrieve", "hello world"])
        assert cfg == {}
        assert argv[1:] == ["--retrieve", "hello world"]

    def test_question_only_preserved(self):
        """A plain question with no flags is not touched."""
        cfg, argv = _run(["rag_runner.py", "what is forecasting?"])
        assert cfg == {}
        assert argv[1:] == ["what is forecasting?"]
