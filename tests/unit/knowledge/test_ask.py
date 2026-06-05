"""Cited-answer assembly, with generation injected (no network)."""

from services.knowledge import ask
from services.knowledge.schema import SearchHit


def _hit(chunk_id, document_id, filename, text, score):
    return SearchHit(
        chunk_id=chunk_id,
        document_id=document_id,
        filename=filename,
        text=text,
        score=score,
    )


def test_no_hits_refuses():
    result = ask.answer_question("anything", [], generate=lambda *a, **k: "should not run")
    assert result.no_answer is True
    assert result.answer == ""
    assert result.citations == []
    assert result.model is None


def test_answer_assembles_citations():
    hits = [
        _hit(1, 10, "vat.txt", "Thailand VAT is 7 percent.", 0.9),
        _hit(2, 11, "wht.txt", "WHT on services is 3 percent.", 0.5),
    ]
    captured = {}

    def fake_generate(prompt, *, system=None, temperature=0.2):
        captured["prompt"] = prompt
        captured["system"] = system
        return "VAT is 7% [1]."

    result = ask.answer_question("VAT rate?", hits, generate=fake_generate)
    assert result.no_answer is False
    assert result.answer == "VAT is 7% [1]."
    assert [c["index"] for c in result.citations] == [1, 2]
    assert result.citations[0]["filename"] == "vat.txt"
    assert result.model == ask.generation.MODEL
    # the prompt carries the numbered sources and the question
    assert "[1] (vat.txt)" in captured["prompt"]
    assert "VAT rate?" in captured["prompt"]
    assert captured["system"] == ask.SYSTEM_PROMPT


def test_sentinel_refusal_with_hits_is_no_answer():
    hits = [_hit(1, 10, "vat.txt", "Thailand VAT is 7 percent.", 0.4)]
    result = ask.answer_question(
        "Mars office pet policy?", hits, generate=lambda *a, **k: ask.NO_ANSWER_SENTINEL
    )
    assert result.no_answer is True
    assert result.answer == ""
    assert result.citations == []


def test_uncited_answer_with_hits_is_no_answer():
    # Model replied in prose but grounded nothing (no [n]); must refuse, not bill.
    hits = [_hit(1, 10, "vat.txt", "Thailand VAT is 7 percent.", 0.3)]
    result = ask.answer_question(
        "Pluto paint color?",
        hits,
        generate=lambda *a, **k: "I do not have enough information.",
    )
    assert result.no_answer is True
    assert result.citations == []


from tests.unit.knowledge._pytest_adapter import build_case  # noqa: E402

TestAsk = build_case(globals(), "TestAsk")
