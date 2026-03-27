import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from services.short_term_state_service import detect_short_term_state


def test_detect_short_term_state_empty():
    assert detect_short_term_state("") is None


def test_detect_short_term_state_sick():
    result = detect_short_term_state("我感冒了，今天很难受")
    assert result is not None
    assert result["state"] == "sick"
    assert "expires_at" in result


def test_detect_short_term_state_travel():
    result = detect_short_term_state("这两天出差住酒店")
    assert result is not None
    assert result["state"] == "travel"
