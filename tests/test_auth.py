from app.extensions import db
from app.models import SkillRating, User


def test_register_initializes_account_and_ratings(client, app):
    response = client.post("/register", data={"email": "learner@example.com", "password": "password123", "level": "B1"})
    assert response.status_code == 302
    with app.app_context():
        user = db.session.scalar(db.select(User).filter_by(email="learner@example.com"))
        assert user is not None
        ratings = db.session.scalars(db.select(SkillRating).filter_by(user_id=user.id)).all()
        assert {rating.skill for rating in ratings} == {"grammar", "vocab", "writing"}
        assert {rating.rating for rating in ratings} == {1000.0}


def test_login_rejects_bad_credentials(client):
    client.post("/register", data={"email": "learner@example.com", "password": "password123", "level": "A1"})
    response = client.post("/login", data={"email": "learner@example.com", "password": "wrongpass"})
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data
