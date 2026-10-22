import sys
from server import lookup_word, find_words, check_spelling, grammar_features

def test_mcp_tools():
    print("=== TEST 1: lookup_word ===")
    res_ord = lookup_word("cykler")
    print("Opslag 'cykler':", res_ord)
    assert res_ord["is_valid_danish_word"] is True

    res_uregel = lookup_word("afbrød")
    print("Opslag 'afbrød':", res_uregel)
    assert res_uregel["irregular_verb"] is not None

    print("\n=== TEST 2: check_spelling ===")
    res_typo = check_spelling("accellerere")
    print("Stavefejl 'accellerere':", res_typo)
    assert res_typo["is_known_spelling_error"] is True
    assert res_typo["official_corrections"][0]["korrekt_form"] == "accelerere"

    print("\n=== TEST 3: find_words ===")
    res_find = find_words(pattern="b*ing", length=8, limit=5)
    print("Find 'b*ing' (længde 8):", res_find)
    assert len(res_find["words"]) > 0

    res_wordle = find_words(pattern="k?tte", is_wordle=True)
    print("Find Wordle 'k?tte':", res_wordle)
    assert "katte" in res_wordle["words"]

    print("\n=== TEST 4: grammar_features ===")
    res_valgfrit = grammar_features("valgfrit_koen", query="folie")
    print("Valgfrit køn 'folie':", res_valgfrit)
    assert any("alufolie" in r["word"] for r in res_valgfrit["results"])

    res_verb = grammar_features("uregelmaessige_verber", query="adlyde")
    print("Uregelmæssigt verbum 'adlyde':", res_verb)
    assert len(res_verb["results"]) > 0

    print("\n>>> ALLE TESTS BESTÅET! <<<")

if __name__ == "__main__":
    test_mcp_tools()
