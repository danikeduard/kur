# Adaptive level model

The learner state is `S = (R_grammar, R_vocab, R_writing, E)`, where each
`R` is a skill rating and `E` is the accumulated error-topic distribution.
CEFR centres are A1=600, A2=800, B1=1000, B2=1200, C1=1400, C2=1600.

For valid message index `n`, observation confidence `c`, and observed centre
`R_obs`, the update is:

`delta = clamp(0.12 * w_n * c * (R_obs - R), -80, 80)`

`R_new = R + delta`, where `w_n=2` for the first five valid messages and `1`
afterwards. Confidence below 0.3 skips an update. The early weight corrects a
poor self-assessment quickly without making later noisy observations dominate.
Displayed labels use 25-point hysteresis around each boundary.
