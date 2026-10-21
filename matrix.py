"""Prints a table of which role can reach which endpoint. Run with: python matrix.py"""

from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)

LOGINS = [("player (pat)", "pat", "player123"), ("parent (pam)", "pam", "parent123"), ("admin (ada)", "ada", "admin123")]

CALLS = [
    ("GET /lessons", "GET", "/lessons"),
    ("POST /progress/complete-lesson", "POST", "/progress/complete-lesson"),
    ("GET /children/pat/progress", "GET", "/children/pat/progress"),
    ("GET /children/lee/progress", "GET", "/children/lee/progress"),
    ("GET /admin/users", "GET", "/admin/users"),
]


def label(code):
    return {200: "200 allowed", 401: "401 no login", 403: "403 BLOCKED"}.get(code, str(code))


def main():
    headers = {}
    for title, user, pw in LOGINS:
        token = client.post("/login", json={"username": user, "password": pw}).json()["token"]
        headers[title] = {"Authorization": f"Bearer {token}"}

    width = 32
    print("CoinQuest RBAC matrix (what each role gets back)\n")
    print(f"{'Endpoint':<{width}}" + "".join(f"{t:<18}" for t, _, _ in LOGINS))
    print("-" * (width + 18 * len(LOGINS)))
    for name, method, path in CALLS:
        row = f"{name:<{width}}"
        for title, _, _ in LOGINS:
            r = client.request(method, path, headers=headers[title])
            row += f"{label(r.status_code):<18}"
        print(row)
    print(f"{'(no login at all)':<{width}}" + label(client.get('/lessons').status_code))


if __name__ == "__main__":
    main()
