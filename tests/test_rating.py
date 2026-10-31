import pytest

from app.rating import (
    displayed_level,
    initial_ratings,
    is_valid_message,
    level_to_rating,
    overall_rating,
    rating_to_level,
    update_rating,
)


def test_initialization_and_mapping_boundaries():
    assert initial_ratings("C1") == {"grammar": 1400.0, "vocab": 1400.0, "writing": 1400.0}
    assert level_to_rating("a2") == 800
    assert rating_to_level(699.99) == "A1"
    assert rating_to_level(700) == "A2"
    assert rating_to_level(899.99) == "A2"
    assert rating_to_level(900) == "B1"
    assert rating_to_level(1500) == "C2"


def test_weight_is_two_for_first_five_and_one_after():
    first, first_weight = update_rating(1000, "A2", 1, 1)
    sixth, sixth_weight = update_rating(1000, "A2", 1, 6)
    assert first_weight == 2
    assert sixth_weight == 1
    assert 1000 - first == 2 * (1000 - sixth)


def test_delta_is_clamped():
    updated, _ = update_rating(1600, "A1", 1, 1)
    assert updated == 1520


def test_low_confidence_skips_update():
    assert update_rating(1000, "C2", 0.29, 1)[0] == 1000


def test_invalid_messages_do_not_qualify_for_rating():
    assert not is_valid_message("/analysis please explain this")
    assert not is_valid_message("Too short")
    assert is_valid_message("I enjoy reading books every evening.")


def test_hysteresis_prevents_flapping():
    assert displayed_level(905, "A2") == "A2"
    assert displayed_level(925, "A2") == "B1"
    assert displayed_level(880, "B1") == "B1"
    assert displayed_level(875, "B1") == "A2"


def test_overall_weighted_rating():
    assert overall_rating({"grammar": 1000, "vocab": 1200, "writing": 1400}) == pytest.approx(1180)


def test_convergence_is_faster_during_early_window():
    early = 1400.0
    late = 1400.0
    for index in range(1, 6):
        early, _ = update_rating(early, "A2", 1, index)
    for index in range(6, 11):
        late, _ = update_rating(late, "A2", 1, index)
    assert abs(1400 - early) > abs(1400 - late)
    assert early < 1400 and late < 1400
