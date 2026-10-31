from types import SimpleNamespace


class FakeGroq:
    def __init__(self, **kwargs):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        if kwargs.get("response_format", {}).get("type") == "json_object":
            content = '{"is_english": true, "skills": {"grammar": {"level": "B1", "confidence": 0.9}, "vocab": {"level": "B1", "confidence": 0.8}, "writing": {"level": "B1", "confidence": 0.7}}, "errors": []}'
        else:
            content = "Nice work! Can you tell me more? 🙂"
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_chat_persists_message_and_returns_levels(client, app, monkeypatch):
    client.post("/register", data={"email": "chat@example.com", "password": "password123", "level": "A2"})
    monkeypatch.setattr("app.routes.Groq", FakeGroq)
    response = client.post("/api/chat", json={"content": "I like reading books every evening."})
    assert response.status_code == 200
    assert response.json["reply"].startswith("Nice work")
    assert response.json["levels"]["grammar"] == "A2"
