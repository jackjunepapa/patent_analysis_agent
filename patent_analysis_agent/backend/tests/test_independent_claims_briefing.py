"""format_independent_claims_briefing for invention summary prompt."""

from phase_invention_analysis import format_independent_claims_briefing


def test_briefing_includes_claim1_from_full_when_missing_in_list():
    meta = [
        {
            "source_file": "inv.pdf",
            "jurisdiction": "US",
            "claim1_full": "1. A device comprising: a housing;",
            "independent_claims": [{"claim_num": 11, "text": "11. A method comprising: step A;", "preview": ""}],
        }
    ]
    s = format_independent_claims_briefing(meta, max_per_claim=5000)
    assert "inv.pdf" in s
    assert "제1항" in s or "Claim 1" in s
    assert "11" in s
    assert "housing" in s.lower() or "method" in s.lower()
