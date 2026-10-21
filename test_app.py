"""Automated tests for the CoinQuest RBAC demo. Run with: pytest -v"""

import copy

import pytest
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def fresh_data():
    """Reset the fake data before every test so tests don't affect each other."""
    users = copy.deepcopy(app_module.USERS)
    progress = copy.deepcopy(app_module.PROGRESS)
    app_module.TOKENS.clear()
    yield
    app_module.USERS.clear()
    app_module.USERS.update(users)
    app_module.PROGRESS.clear()
    app_module.PROGRESS.update(progress)


def login(username, password):
    r = client.post("/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


PASSWORDS = {"pat": "player123", "pam": "parent123", "ada": "admin123"}


def test_wrong_password_is_401():
    r = client.post("/login", json={"username": "pat", "password": "nope"})
    assert r.status_code == 401


def test_no_token_is_401():
    assert client.get("/lessons").status_code == 401


def test_bad_token_is_401():
    r = client.get("/lessons", headers={"Authorization": "Bearer fake"})
    assert r.status_code == 401


def test_everyone_can_read_lessons():
    for name, pw in PASSWORDS.items():
        assert client.get("/lessons", headers=login(name, pw)).status_code == 200


def test_player_can_complete_lesson():
    r = client.post("/progress/complete-lesson", headers=login("pat", "player123"))
    assert r.status_code == 200
    assert r.json()["lessons_completed"] == 4


def test_parent_cannot_complete_lesson():
    r = client.post("/progress/complete-lesson", headers=login("pam", "parent123"))
    assert r.status_code == 403


def test_parent_can_see_own_child():
    r = client.get("/children/pat/progress", headers=login("pam", "parent123"))
    assert r.status_code == 200


def test_parent_cannot_see_other_child():
    r = client.get("/children/lee/progress", headers=login("pam", "parent123"))
    assert r.status_code == 403


def test_player_cannot_see_children_progress():
    r = client.get("/children/pat/progress", headers=login("pat", "player123"))
    assert r.status_code == 403


def test_player_cannot_use_admin_endpoints():
    h = login("pat", "player123")
    assert client.get("/admin/users", headers=h).status_code == 403
    assert client.delete("/admin/users/lee", headers=h).status_code == 403


def test_parent_cannot_use_admin_endpoints():
    assert client.get("/admin/users", headers=login("pam", "parent123")).status_code == 403


def test_admin_can_list_and_delete_users():
    h = login("ada", "admin123")
    r = client.get("/admin/users", headers=h)
    assert r.status_code == 200
    assert all("password" not in u for u in r.json())
    assert client.delete("/admin/users/lee", headers=h).status_code == 200


def test_admin_cannot_delete_self():
    h = login("ada", "admin123")
    assert client.delete("/admin/users/ada", headers=h).status_code == 400
