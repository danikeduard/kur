"""Report real-user rating snapshots after 5, 10, and 20 valid messages."""

from sqlalchemy import create_engine, text


def main() -> None:
    from app.config import Config
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    query = text("""SELECT u.id, u.self_level, re.skill, re.rating_after,
                    ROW_NUMBER() OVER (PARTITION BY re.user_id ORDER BY re.message_id) AS n
                    FROM rating_event re JOIN "user" u ON u.id = re.user_id""")
    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()
    if not rows:
        print("Warning: no rating events; collect real learner data first.")
        return
    print("user_id,self_level,skill,rating_after_5,rating_after_10,rating_after_20")
    grouped = {}
    for user_id, self_level, skill, rating, n in rows:
        grouped.setdefault((user_id, self_level, skill), {})[int(n)] = rating
    for (user_id, self_level, skill), values in sorted(grouped.items()):
        print(f"{user_id},{self_level},{skill},{values.get(5, '')},{values.get(10, '')},{values.get(20, '')}")
    if len({key[0] for key in grouped}) < 10:
        print("Warning: fewer than 10 users; convergence comparisons may be unstable.")


if __name__ == "__main__":
    main()
