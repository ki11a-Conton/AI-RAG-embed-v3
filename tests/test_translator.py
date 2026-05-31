import sys
import types

from lib.query_enhancer import OfflineTranslator


def _install_fake_argos(monkeypatch, result=None, error=None):
    argos_module = types.ModuleType("argostranslate")
    translate_module = types.ModuleType("argostranslate.translate")

    def translate(question, from_lang, to_lang):
        if error:
            raise error
        return result

    translate_module.translate = translate
    argos_module.translate = translate_module
    monkeypatch.setitem(sys.modules, "argostranslate", argos_module)
    monkeypatch.setitem(sys.modules, "argostranslate.translate", translate_module)


def test_enhance_returns_translated_string(monkeypatch):
    _install_fake_argos(monkeypatch, result="what is the time constant")
    translator = OfflineTranslator(from_lang="zh", to_lang="en")

    result = translator.enhance("\u4ec0\u4e48\u662f\u65f6\u95f4\u5e38\u6570")

    assert result == "what is the time constant"


def test_enhance_fallback_on_exception(monkeypatch):
    _install_fake_argos(monkeypatch, error=Exception("model not found"))
    translator = OfflineTranslator(from_lang="zh", to_lang="en")

    question = "\u4ec0\u4e48\u662f\u65f6\u95f4\u5e38\u6570"
    result = translator.enhance(question)

    assert result == question


def test_enhance_empty_string():
    translator = OfflineTranslator()

    result = translator.enhance("")

    assert result == ""


def test_offline_translator_label_is_translated_question():
    translator = OfflineTranslator()

    assert translator.label == "Translated Question"


def test_enhance_short_followup_sends_only_question_to_argos(monkeypatch):
    captured_inputs = []

    argos_module = types.ModuleType("argostranslate")
    translate_module = types.ModuleType("argostranslate.translate")

    def fake_translate(question, from_lang, to_lang):
        captured_inputs.append(question)
        return "how to use it"

    translate_module.translate = fake_translate
    argos_module.translate = translate_module
    monkeypatch.setitem(sys.modules, "argostranslate", argos_module)
    monkeypatch.setitem(sys.modules, "argostranslate.translate", translate_module)

    translator = OfflineTranslator(from_lang="zh", to_lang="en")
    result = translator.enhance(
        "它怎么用",
        history=[{"role": "user", "content": "ETS模型"}],
    )

    # Argos received only the Chinese question, not the "Following up on" wrapper
    assert len(captured_inputs) == 1
    assert captured_inputs[0] == "它怎么用"

    # Output includes the history wrapper around the translated question
    assert "Following up on" in result
    assert "ETS模型" in result
    assert "how to use it" in result


def test_enhance_short_followup_wraps_output(monkeypatch):
    _install_fake_argos(monkeypatch, result="exponential smoothing")
    translator = OfflineTranslator()

    result = translator.enhance(
        "\u6307\u6570\u5e73\u6ed1",
        history=[{"role": "user", "content": "\u4e0a\u4e00\u4e2a\u95ee\u9898"}],
    )

    assert result == "Following up on '\u4e0a\u4e00\u4e2a\u95ee\u9898': exponential smoothing"


def test_enhance_short_followup_uses_context():
    translator = OfflineTranslator()

    resolved = translator._resolve_pronouns(
        "它怎么用",
        history=[{"role": "user", "content": "ETS模型"}],
    )

    assert "ETS" in resolved
    assert "它怎么用" in resolved


def test_enhance_returns_original_if_empty_result(monkeypatch):
    _install_fake_argos(monkeypatch, result="")
    translator = OfflineTranslator()

    question = "\u6307\u6570\u5e73\u6ed1"
    result = translator.enhance(question)

    assert result == question


def test_zh_to_en_translator_leaves_english_query_unchanged(monkeypatch):
    _install_fake_argos(monkeypatch, error=AssertionError("should not translate"))
    translator = OfflineTranslator(from_lang="zh", to_lang="en")

    result = translator.enhance("time constant")

    assert result == "time constant"
