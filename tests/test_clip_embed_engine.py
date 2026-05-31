"""Focused tests for CLIPEmbedEngine – fully mocked, no model download, no network."""

import sys
import math
from unittest.mock import MagicMock
import pytest


# ---------------------------------------------------------------------------
# Minimal stubs so CLIPEmbedEngine can run without real torch / PIL
# ---------------------------------------------------------------------------

class _FakeTensor:
    """Tensor stub that supports norm / div / squeeze / tolist."""

    def __init__(self, values):
        self._values = list(values)

    def norm(self, dim=-1, keepdim=True):
        n = math.sqrt(sum(v * v for v in self._values))
        return _FakeTensor([n])

    def __truediv__(self, other):
        if isinstance(other, _FakeTensor):
            denom = other._values[0] if other._values else 1.0
        else:
            denom = other
        if denom == 0:
            denom = 1.0
        return _FakeTensor([v / denom for v in self._values])

    def squeeze(self, dim=None):
        return self

    def tolist(self):
        return self._values


class _FakeNoGrad:
    """Context manager stub for torch.no_grad()."""

    def __enter__(self):
        return None

    def __exit__(self, *args):
        return False


# ---------------------------------------------------------------------------
# Module-level fixtures – inject fakes before any lazy import runs
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _inject_fake_modules():
    """Ensures every test in this module runs against fake deps."""

    fake_torch = MagicMock()
    fake_torch.no_grad.return_value = _FakeNoGrad()

    fake_transformers = MagicMock()
    fake_clip_model_cls = MagicMock()
    fake_clip_proc_cls = MagicMock()
    fake_transformers.CLIPModel = fake_clip_model_cls
    fake_transformers.CLIPProcessor = fake_clip_proc_cls

    fake_pil_image = MagicMock()
    fake_pil = MagicMock()
    fake_pil.Image = fake_pil_image

    # Stash originals so we can restore after each test
    orig = {}
    for name, fake in (
        ("torch", fake_torch),
        ("transformers", fake_transformers),
        ("PIL", fake_pil),
        ("PIL.Image", fake_pil_image),
    ):
        orig[name] = sys.modules.get(name)
        sys.modules[name] = fake

    # Expose the fakes dict to tests that request the "fakes" fixture
    fakes_dict = {
        "torch": fake_torch,
        "transformers": fake_transformers,
        "clip_model_cls": fake_clip_model_cls,
        "clip_proc_cls": fake_clip_proc_cls,
        "pil": fake_pil,
        "pil_image": fake_pil_image,
    }

    yield fakes_dict

    # Restore sys.modules
    for name, mod in orig.items():
        if mod is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = mod


@pytest.fixture
def fakes(_inject_fake_modules):
    """Alias so tests can reference the fake module mocks by name."""
    return _inject_fake_modules


@pytest.fixture
def CLIPEmbedEngine():
    """Import under the fake-module regime."""
    from lib.embed_engine import CLIPEmbedEngine

    return CLIPEmbedEngine


# ===================================================================
# Tests – grouped logically
# ===================================================================


class TestCLIPEmbedEngineDefaults:
    def test_default_model_name(self, CLIPEmbedEngine):
        engine = CLIPEmbedEngine()
        assert engine.model_name == "openai/clip-vit-base-patch32"

    def test_custom_model_name(self, CLIPEmbedEngine):
        engine = CLIPEmbedEngine(model_name="laion/CLIP-ViT-H-14-laion2B-s32B-b79K")
        assert engine.model_name == "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"

    def test_not_loaded_initially(self, CLIPEmbedEngine):
        engine = CLIPEmbedEngine()
        assert engine._model is None
        assert engine._processor is None


class TestCLIPEmbedEngineEmbedText:

    def test_returns_plain_floats(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_text_features.return_value = _FakeTensor([0.1, 0.2, 0.3])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()

        engine = CLIPEmbedEngine()
        result = engine.embed_text("a photo of a cat")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_sets_model_to_eval(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_text_features.return_value = _FakeTensor([0.5])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()

        engine = CLIPEmbedEngine()
        engine.embed_text("test")
        fake_model.eval.assert_called_once()

    def test_uses_custom_model_name_for_pretrained(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_text_features.return_value = _FakeTensor([0.5])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()

        engine = CLIPEmbedEngine(model_name="custom/model")
        engine.embed_text("x")
        fakes["clip_model_cls"].from_pretrained.assert_called_with("custom/model")

    def test_embed_text_normalized(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_text_features.return_value = _FakeTensor([3.0, 4.0])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()

        engine = CLIPEmbedEngine()
        result = engine.embed_text("any text")
        # Should be L2-normalized → norm ≈ 1.0
        norm = math.sqrt(sum(v * v for v in result))
        assert abs(norm - 1.0) < 1e-6, f"norm={norm}, expected 1.0"


class TestCLIPEmbedEngineEmbedImage:

    def test_returns_plain_floats(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_image_features.return_value = _FakeTensor([0.5, 0.6, 0.7])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()
        fake_img = MagicMock()
        fake_img.convert.return_value = fake_img
        fakes["pil_image"].open.return_value = fake_img

        engine = CLIPEmbedEngine()
        result = engine.embed_image(b"fake_bytes")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_image_converted_to_rgb(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_image_features.return_value = _FakeTensor([0.5])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()
        fake_img = MagicMock()
        fake_img.convert.return_value = fake_img
        fakes["pil_image"].open.return_value = fake_img

        engine = CLIPEmbedEngine()
        engine.embed_image(b"fake_bytes")
        fake_img.convert.assert_called_once_with("RGB")

    def test_embed_image_normalized(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_image_features.return_value = _FakeTensor([3.0, 4.0])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()
        fake_img = MagicMock()
        fake_img.convert.return_value = fake_img
        fakes["pil_image"].open.return_value = fake_img

        engine = CLIPEmbedEngine()
        result = engine.embed_image(b"fake_bytes")
        norm = math.sqrt(sum(v * v for v in result))
        assert abs(norm - 1.0) < 1e-6


class TestCLIPEmbedEngineLazyLoading:

    def test_lazy_load_only_happens_once(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_text_features.return_value = _FakeTensor([0.1, 0.2])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()

        engine = CLIPEmbedEngine()
        engine.embed_text("first")
        engine.embed_text("second")
        assert fakes["clip_model_cls"].from_pretrained.call_count == 1
        assert fakes["clip_proc_cls"].from_pretrained.call_count == 1

    def test_not_reloaded_for_image_after_text(self, CLIPEmbedEngine, fakes):
        fake_model = MagicMock()
        fake_model.get_text_features.return_value = _FakeTensor([0.1])
        fake_model.get_image_features.return_value = _FakeTensor([0.2])
        fakes["clip_model_cls"].from_pretrained.return_value = fake_model
        fakes["clip_proc_cls"].from_pretrained.return_value = MagicMock()
        fake_img = MagicMock()
        fake_img.convert.return_value = fake_img
        fakes["pil_image"].open.return_value = fake_img

        engine = CLIPEmbedEngine()
        engine.embed_text("hello")
        engine.embed_image(b"bytes")
        # Still only one load
        assert fakes["clip_model_cls"].from_pretrained.call_count == 1


class TestExistingEmbedEngineUntouched:
    """Smoke-test: CLIP changes did not break the original EmbedEngine class."""

    def test_class_still_exists(self):
        from lib.embed_engine import EmbedEngine

        assert EmbedEngine is not None

    def test_expected_methods(self):
        from lib.embed_engine import EmbedEngine

        for method in ("get_embedding", "embed_documents", "embed_batch"):
            assert hasattr(EmbedEngine, method), f"EmbedEngine missing {method}"
