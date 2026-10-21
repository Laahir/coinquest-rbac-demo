# CoinQuest RBAC Demo

A small API I built to practice backend API design, with a focus on role-based access control (RBAC). CoinQuest is a made-up money-literacy game. It is not connected to any real project code.

## Roles

| Role   | What they can do |
|--------|------------------|
| player | read lessons, complete lessons for themselves |
| parent | read lessons, view progress for their own child only |
| admin  | read lessons, list and delete users |

Wrong or missing login returns 401. Right login but wrong role returns 403.

## Run it

```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Then open http://127.0.0.1:8000/docs

Test logins: pat / player123, pam / parent123, ada / admin123

## Tests

```
pytest -v
python matrix.py
```
