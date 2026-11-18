from datetime import date, timedelta

import pytest

from app import app, db, Appointment, seed_services


@pytest.fixture
def client():
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        seed_services()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def future_date():
    return (date.today() + timedelta(days=1)).isoformat()


def test_services_are_seeded(client):
    response = client.get("/api/servicos")
    assert response.status_code == 200
    assert len(response.get_json()) == 3


def test_create_and_detect_conflict(client):
    payload = {"service_id": 1, "data": future_date(), "hora": "09:00",
               "nome": "João Silva", "telefone": "11999999999"}
    first = client.post("/api/agendamentos", json=payload)
    assert first.status_code == 201
    second = client.post("/api/agendamentos", json=payload)
    assert second.status_code == 409


def test_invalid_phone(client):
    response = client.post("/api/agendamentos", json={
        "service_id": 1, "data": future_date(), "hora": "10:00",
        "nome": "Maria Souza", "telefone": "123"
    })
    assert response.status_code == 400


def test_occupied_slots(client):
    payload = {"service_id": 1, "data": future_date(), "hora": "11:30",
               "nome": "Carlos Lima", "telefone": "21988887777"}
    assert client.post("/api/agendamentos", json=payload).status_code == 201
    response = client.get("/api/agendamentos", query_string={"data": future_date()})
    assert "11:30" in response.get_json()["ocupados"]
