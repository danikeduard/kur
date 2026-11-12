# Changelog

## Unreleased

- **P2 rating assumption:** Keep the previously requested 2.5× CEFR rating scale and apply Kalman gain directly on that scale. The 120-point cap is also on the expanded scale; the model does not divide movement by 2.5.
- **P0 daily-limit assumption:** A chat turn consumes the daily allowance only after it completes. The date boundary remains UTC, matching stored timestamps.
- **P0 provider fix:** The configured OpenAI provider uses the official OpenAI SDK and requires `OPENAI_API_KEY`; custom OpenAI-compatible endpoints continue to use `OPENAI_BASE_URL`.
- **P0 conversation behavior:** Duplicated messages are history only and never count as fresh rating evidence. Conversation pagination follows the existing pinned, updated-at, id sort order.
