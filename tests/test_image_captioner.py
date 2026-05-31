"""tests/test_image_captioner.py — fully mocked, no network."""
import base64
from unittest.mock import MagicMock

from lib.image_captioner import ImageCaptioner


# ──────────────────────────────────────────────
# ImageCaptioner unit tests
# ──────────────────────────────────────────────


class TestImageCaptioner:
    """All tests use a mock client — zero network calls."""

    @staticmethod
    def _make_captioner(model="test-vision-model"):
        cap = ImageCaptioner(
            api_key="dummy-test-key",
            base_url="https://test.example.com/v1",
            model=model,
        )
        # Replace the real client with a mock
        cap._client = MagicMock()
        return cap

    @staticmethod
    def _set_caption_response(cap, text: str):
        resp = MagicMock()
        resp.choices = [MagicMock(message=MagicMock(content=text))]
        cap._client.chat.completions.create.return_value = resp

    # ── basic behaviour ──────────────────────

    def test_init_stores_model(self):
        cap = self._make_captioner("gpt-4o-mini")
        assert cap._model == "gpt-4o-mini"
        assert cap._client is not None

    def test_caption_returns_text(self):
        cap = self._make_captioner()
        self._set_caption_response(cap, "A diagram of a neural network.")
        result = cap.caption(b"\x89PNGfake")
        assert result == "A diagram of a neural network."

    def test_caption_empty_response_returns_empty_string(self):
        cap = self._make_captioner()
        self._set_caption_response(cap, None)  # None content
        result = cap.caption(b"\x89PNGfake")
        assert result == ""

        self._set_caption_response(cap, "")   # empty content
        result = cap.caption(b"\x89PNGfake")
        assert result == ""

    # ── vision request structure ────────────

    def test_caption_builds_vision_request_model(self):
        cap = self._make_captioner("my-vision-llm")
        self._set_caption_response(cap, "ok")
        cap.caption(b"\x89PNGfake")

        cap._client.chat.completions.create.assert_called_once()
        kwargs = cap._client.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "my-vision-llm"

    def test_caption_builds_vision_request_messages(self):
        cap = self._make_captioner()
        self._set_caption_response(cap, "ok")
        cap.caption(b"\x89PNGfake")

        kwargs = cap._client.chat.completions.create.call_args.kwargs
        messages = kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "image captioning" in messages[0]["content"].lower()

        assert messages[1]["role"] == "user"
        assert isinstance(messages[1]["content"], list)

    def test_caption_includes_base64_image_url(self):
        cap = self._make_captioner()
        self._set_caption_response(cap, "ok")
        image_bytes = b"\x89PNG\x00\x0D\x0A\x1A\x0Ahello world"
        cap.caption(image_bytes)

        kwargs = cap._client.chat.completions.create.call_args.kwargs
        user_content = kwargs["messages"][1]["content"]
        image_part = user_content[1]
        assert image_part["type"] == "image_url"
        url = image_part["image_url"]["url"]
        assert url.startswith("data:image/png;base64,")
        b64_part = url.split(",", 1)[1]
        decoded = base64.b64decode(b64_part)
        assert decoded == image_bytes

    # ── context_hint ────────────────────────

    def test_caption_with_context_hint(self):
        cap = self._make_captioner()
        self._set_caption_response(cap, "A bar chart.")
        cap.caption(b"\x89PNGfake", context_hint="From page 5 of report.pdf")

        kwargs = cap._client.chat.completions.create.call_args.kwargs
        user_text = kwargs["messages"][1]["content"][0]["text"]
        assert "Context: From page 5 of report.pdf" in user_text
        assert "describe this image" in user_text.lower()

    def test_caption_without_context_hint(self):
        cap = self._make_captioner()
        self._set_caption_response(cap, "ok")
        cap.caption(b"\x89PNGfake")

        kwargs = cap._client.chat.completions.create.call_args.kwargs
        user_text = kwargs["messages"][1]["content"][0]["text"]
        assert "Context:" not in user_text

    # ── no secrets in repr ──────────────────

    def test_repr_does_not_leak_api_key(self):
        cap = ImageCaptioner(
            api_key="dummy-super-secret-12345",
            base_url="https://test.example.com/v1",
            model="x",
        )
        r = repr(cap)
        assert "dummy-super-secret" not in r
        assert "x" in r  # model name is safe

    def test_str_does_not_leak_api_key(self):
        cap = ImageCaptioner(
            api_key="dummy-super-secret-12345",
            base_url="https://test.example.com/v1",
            model="x",
        )
        s = str(cap)
        assert "dummy-super-secret" not in s

    # ── error handling ──────────────────────

    def test_caption_propagates_client_error(self):
        cap = self._make_captioner()
        cap._client.chat.completions.create.side_effect = RuntimeError("API down")
        try:
            cap.caption(b"\x89PNGfake")
            assert False, "should have raised"
        except RuntimeError:
            pass
