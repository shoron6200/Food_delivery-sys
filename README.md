# Food Delivery System (Backend)

Varsity project: ekta food delivery platform er backend API, **Python + FastAPI + SQLite** diye.
Full plan ar unique feature gula [PLAN.md](PLAN.md) te ache.

## Ekhon porjonto ki ache

| Step | Ki | Lesson |
|---|---|---|
| 1 | Project setup, FastAPI basics | [01-setup-ar-fastapi-basics.md](docs/lessons/01-setup-ar-fastapi-basics.md) |
| 2 | Database, `users` table | [02-database-ar-models.md](docs/lessons/02-database-ar-models.md) |
| 3 | Register, login (JWT), `/me` | [03-auth-password-ar-jwt.md](docs/lessons/03-auth-password-ar-jwt.md) |
| 4 | Restaurant, menu, role permission | [04-restaurant-ar-menu.md](docs/lessons/04-restaurant-ar-menu.md) |

Porer step: Cart + Honest Price.

## Nijer computer e chalano

Python 3.10 ba tar porer version lagbe.

```bash
# 1. Virtual environment banao ar chalu koro
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Package install koro
pip install -r requirements.txt

# 3. .env file banao
cp .env.example .env             # Windows: copy .env.example .env

# 4. Ekta secret key banao, tarpor .env file e SECRET_KEY= er pore boshao
python -c "import secrets; print(secrets.token_hex(32))"

# 5. Server chalao
uvicorn app.main:app --reload
```

Tarpor browser e jao: **http://127.0.0.1:8000/docs**. Okhane shob API dekhte ar try korte parbe.

## Test chalano

```bash
python -m pytest
```

## Folder structure

```
app/
├── main.py           # app shuru hoy ekhan theke
├── core/
│   ├── config.py     # settings (.env theke pore)
│   └── security.py   # password hash, JWT token
├── db/
│   └── database.py   # database connection, session
├── models/           # database table (SQLAlchemy)
├── schemas/          # request/response er shape (Pydantic)
└── api/
    ├── deps.py       # shared dependency (current user)
    └── v1/           # endpoint gula (auth, restaurants, pore order...)
tests/                # automatic test
docs/lessons/         # step by step lesson (Banglish)
```
