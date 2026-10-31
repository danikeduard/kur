"""Create the tables used by the Flask SQLAlchemy application."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db


def main() -> None:
    app = create_app()
    with app.app_context():
        db.create_all()
    print("LinguaPath application tables are ready.")


if __name__ == "__main__":
    main()
