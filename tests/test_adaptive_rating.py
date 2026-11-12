from app.rating import (
    P0,
    SkillState,
    blend_observation,
    density_rating,
    effective_confidence,
    kalman_update,
    level_to_rating,
)


def test_kalman_worked_example():
    state = SkillState(level_to_rating("C1"), P0)
    ratings = []
    for _ in range(7):
        state, _ = kalman_update(state, level_to_rating("A2"), effective_confidence(0.8, 14))
        ratings.append(round(state.r))
    assert ratings == [1280, 1160, 1078, 1025, 987, 959, 937]


def test_length_confidence_and_skip():
    assert effective_confidence(0.8, 4) == 0.8 * 4 / 12
    assert effective_confidence(0.8, 12) == 0.8
    state = SkillState(1000, P0)
    updated, info = kalman_update(state, 1600, effective_confidence(0.8, 4))
    assert updated == state
    assert info["skipped"] is True


def test_density_only_lowers_long_observations():
    assert density_rating(20, 100) == 600
    lowered, density = blend_observation(1400, 20, 100)
    assert lowered == 1160
    assert density == 600
    assert blend_observation(1400, 0, 100) == (1400, 1600)
    assert blend_observation(1400, 20, 4) == (1400, None)


def test_outlier_guard_confirms_same_direction():
    state = SkillState(1000, P0)
    first, first_info = kalman_update(state, 1600, 0.5)
    second, second_info = kalman_update(first, 1600, 0.5)
    assert first_info["outlier_flag"] == 1
    assert second_info["outlier_flag"] == 2
    assert second.r - first.r > first.r - state.r
    reset, reset_info = kalman_update(second, 1000, 0.8)
    assert reset.last_outlier_sign == 0
    assert reset_info["outlier_flag"] == 0
