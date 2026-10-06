import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHARED_ROOT = PROJECT_ROOT / "shared"
if str(SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(SHARED_ROOT))

from retail_common.text.analyzer import Token, analyze


def test_normalizes_nfkc_and_lowercase():
    result = analyze("Café\u00a0")
    assert [t.term for t in result] == ["café"]


def test_index_mode_rejects_invalid_mode():
    try:
        analyze("hello", mode="bad")
        assert False, "Expected ValueError for invalid mode"
    except ValueError:
        pass


def test_query_mode_rejects_invalid_mode():
    try:
        analyze("hello", mode="search")
        assert False, "Expected ValueError for invalid mode"
    except ValueError:
        pass


def test_validates_stem_choice():
    try:
        analyze("hello", stem="bad")
        assert False, "Expected ValueError for invalid stem"
    except ValueError:
        pass


def test_simple_word_tokens():
    result = analyze("battery is poor")
    assert [t.term for t in result] == ["batteri", "poor"]


def test_hyphenated_word_yields_joined_and_split_tokens():
    result = analyze("battery-life is poor", stem="none")
    terms = [t.term for t in result]
    assert "battery-life" in terms
    assert "battery" in terms
    assert "life" in terms
    assert "poor" in terms


def test_email_stays_single_token():
    result = analyze("Email: support@example.com was sent")
    terms = [t.term for t in result]
    assert "support@example.com" in terms


def test_order_id_stays_single_token():
    result = analyze("Order ORD-10293 arrived")
    terms = [t.term for t in result]
    assert "ord-10293" in terms


def test_model_number_keeps_a15_as_single_token():
    result = analyze("The A15 phone is fast")
    terms = [t.term for t in result]
    assert "a15" in terms
    assert "phon" in terms or "phone" in terms


def test_model_number_keeps_5g_as_single_token():
    result = analyze("The 5G phone is fast")
    terms = [t.term for t in result]
    assert "5g" in terms


def test_stopwords_removed_but_not_negation_words():
    result = analyze("the product is not working and is terrible", stem="none")
    terms = [t.term for t in result]
    assert "not" in terms
    assert "the" not in terms
    assert "and" not in terms
    assert "is" not in terms


def test_stopwords_file_contains_negation_words():
    stopwords = (PROJECT_ROOT / "data" / "stopwords.txt").read_text(encoding="utf-8").splitlines()
    assert "not" in stopwords
    assert "no" in stopwords
    assert "never" in stopwords
    assert "without" in stopwords


def test_porter_stem_simplifies_words():
    result = analyze("running runners runs ran")
    assert "run" in [t.term for t in result]


def test_lemma_mode_reduces_words():
    result = analyze("better best mice", stem="lemma")
    assert any(term in {"good", "better", "best", "mouse"} for term in [t.term for t in result])


def test_none_stem_returns_original():
    result = analyze("running", stem="none")
    assert [t.term for t in result] == ["running"]


def test_punctuation_removed():
    result = analyze("bad!!! product, quality?", stem="none")
    terms = [t.term for t in result]
    assert "bad" in terms
    assert "product" in terms
    assert "quality" in terms


def test_positions_are_zero_indexed_and_non_negative():
    result = analyze("one two three", stem="none")
    positions = [t.position for t in result]
    assert positions == list(range(len(result)))
    assert all(p >= 0 for p in positions)


def test_start_end_cover_correct_spans_for_split_hyphen_token():
    result = analyze("battery-life", stem="none")
    token_map = {t.term: t for t in result}
    assert token_map["battery-life"].start == 0
    assert token_map["battery-life"].end == len("battery-life")
    assert token_map["battery"].start == 0
    assert token_map["life"].start == len("battery-")


def test_sinhala_text_is_preserved():
    result = analyze("නැත වගේ", stem="none")
    assert [t.term for t in result] == ["නැත", "වගේ"]


def test_unicode_letters_in_sinhala_are_not_split():
    result = analyze("නැත", stem="none")
    assert len(result) == 1
    assert result[0].term == "නැත"


def test_query_mode_matches_index_mode_for_scalar_text():
    index_tokens = analyze("battery life", mode="index")
    query_tokens = analyze("battery life", mode="query")
    assert [t.term for t in index_tokens] == [t.term for t in query_tokens]


def test_hyphenated_complaint_keeps_negation_term():
    result = analyze("not-working battery", stem="none")
    terms = [t.term for t in result]
    assert "not" in terms
    assert "working" in terms


def test_order_id_and_email_remain_single_tokens_in_mixed_text():
    result = analyze("Email support@example.com order ORD-10293", stem="none")
    terms = [t.term for t in result]
    assert "support@example.com" in terms
    assert "ord-10293" in terms


def test_analyze_empty_string_returns_empty_list():
    assert analyze("") == []


def test_compare_stemmers_script_runs_without_errors():
    script = PROJECT_ROOT / "scripts" / "compare_stemmers.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_token_dataclass_has_expected_fields():
    token = Token("battery", 0, 0, 6)
    assert token.term == "battery"
    assert token.position == 0
    assert token.start == 0
    assert token.end == 6


def test_english_stopword_removal_for_common_words():
    result = analyze("the quick brown fox jumps over the lazy dog", stem="none")
    terms = [t.term for t in result]
    assert "fox" in terms
    assert "jump" in terms or "jumps" in terms
    assert "the" not in terms


def test_query_mode_preserves_negation_words_even_when_in_stoplist():
    result = analyze("never again without reason", mode="query", stem="none")
    terms = [t.term for t in result]
    assert "never" in terms
    assert "without" in terms


def test_hyphenated_model_names_do_not_break():
    result = analyze("A15-5G battery", stem="none")
    terms = [t.term for t in result]
    assert "a15-5g" in terms or "a15" in terms
    assert "battery" in terms


def test_porter_stem_works_on_plural_and_verbs():
    result = analyze("worries worried worrying")
    assert "worri" in [t.term for t in result]


def test_email_and_order_id_are_not_split_by_punctuation():
    result = analyze("user.name+tag@example.com and ORD-10293", stem="none")
    terms = [t.term for t in result]
    assert "user.name+tag@example.com" in terms
    assert "ord-10293" in terms


def test_hyphenated_words_are_kept_in_order_after_split_expansion():
    result = analyze("battery-life", stem="none")
    assert [t.term for t in result][:3] == ["battery-life", "battery", "life"]
