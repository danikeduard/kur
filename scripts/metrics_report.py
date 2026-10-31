"""Print aggregate API metrics from the configured database."""

import statistics

from sqlalchemy import create_engine, text


def main() -> None:
    from app.config import Config
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT latency_ms, tokens_in, tokens_out, est_cost_usd, user_id FROM api_metric")).fetchall()
    if not rows:
        print("Warning: no logged API metrics; nothing to report.")
        return
    latencies = [float(row[0]) for row in rows]
    costs = [float(row[3] or 0) for row in rows]
    tokens = [(row[1] or 0) + (row[2] or 0) for row in rows]
    active_users = len({row[4] for row in rows if row[4] is not None})
    print(f"messages: {len(rows)}")
    print(f"mean latency ms: {statistics.mean(latencies):.2f}")
    print(f"median latency ms: {statistics.median(latencies):.2f}")
    print(f"p95 latency ms: {sorted(latencies)[max(0, int(len(latencies) * .95) - 1)]:.2f}")
    print(f"mean tokens per message: {statistics.mean(tokens):.2f}")
    print(f"cost per message USD: {statistics.mean(costs):.6f}")
    print(f"cost per active user USD: {sum(costs) / active_users:.6f}" if active_users else "cost per active user USD: n/a")
    print(f"cost per 1000 users USD: {(sum(costs) / active_users * 1000):.2f}" if active_users else "cost per 1000 users USD: n/a")
    if len(rows) < 30:
        print("Warning: sample has fewer than 30 API calls.")


if __name__ == "__main__":
    main()
