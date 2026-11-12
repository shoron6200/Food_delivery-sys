# Food Delivery System (Backend)

Varsity project: ekta food delivery platform er backend API, **Python + FastAPI + SQLite** diye. 4 ta role (customer, vendor, rider, admin), 155 ta automatic test, ar 11 ta Banglish lesson.

## Ki alada

| Feature | Ek line e |
|---|---|
| **Honest Price** | Cart e prothom thekei puro hishab; order e thik oi taka i kate |
| **Late Compensation** | Khabar late hole wallet e nije theke taka, complain chhara |
| **Verified Review** | Shudhu je khabar peyeche shei review dite pare, ek bar |
| **"Tomar jonno"** | Age r order dekhe recommendation, karon shoho |
| **Banglish AI Assistant** | "500 takar moddhe jhal kichu" bolle menu theke bachhe |

## Kothay ki ache

| Tumi chao | Jao |
|---|---|
| Project chalate | niche "Nijer computer e chalano" |
| Shikhte, por por | niche "Lesson" (1 theke 11) |
| Presentation dite | [docs/demo-guide.md](docs/demo-guide.md) |
| Report likhte (diagram, feature, shimabaddhota) | [docs/project-report.md](docs/project-report.md) |
| Puro plan ar future kaj | [PLAN.md](PLAN.md) |

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

# 5. Demo data (4 ta account, 3 ta restaurant) banao
python -m scripts.seed_demo

# 6. Server chalao
uvicorn app.main:app --reload
```

Tarpor browser e jao: **http://127.0.0.1:8000/docs**. Okhane shob API dekhte ar try korte parbe.

Dhap 5 er account gula (password shobar `demo-pass-123`):

| Role | Phone |
|---|---|
| admin | `01700000001` |
| vendor | `01700000002` |
| customer | `01700000003` |
| rider | `01700000004` |

`/docs` er **Authorize** button e `username` er ghore phone dao.

**Shob notun kore shuru korte:** `food_delivery.db` file ta muche dhap 5 abar chalao.

## Test chalano

```bash
python -m pytest
```

## Lesson

Protita lesson e ache: ki banano holo, keno, code er bekkha, Swagger e try, "Nije koro" exercise, ar viva proshno.

| # | Lesson | Ki shikhbe |
|---|---|---|
| 1 | [Setup ar FastAPI basics](docs/lessons/01-setup-ar-fastapi-basics.md) | HTTP, API, endpoint, Swagger |
| 2 | [Database ar models](docs/lessons/02-database-ar-models.md) | ORM, model vs schema, session |
| 3 | [Auth: password ar JWT](docs/lessons/03-auth-password-ar-jwt.md) | Hash, token, `Depends` |
| 4 | [Restaurant ar menu](docs/lessons/04-restaurant-ar-menu.md) | CRUD, foreign key, permission (401/403/404) |
| 5 | [Cart ar Honest Price](docs/lessons/05-cart-ar-honest-price.md) | Services layer, pure function, unit test |
| 6 | [Order ar status flow](docs/lessons/06-order-ar-status-flow.md) | State machine, transaction, race condition |
| 7 | [Rider ar admin](docs/lessons/07-rider-ar-admin.md) | Role, least privilege, route er kromo |
| 8 | [Review ar rating](docs/lessons/08-review-ar-rating.md) | Aggregate, denormalization |
| 9 | [Late Compensation ar wallet](docs/lessons/09-late-compensation-ar-wallet.md) | Datetime, ledger, boundary testing |
| 10 | [Recommendation](docs/lessons/10-recommendation.md) | Content-based filtering, cold start, JOIN |
| 11 | [AI assistant](docs/lessons/11-ai-assistant.md) | LLM, prompt, structured output, rate limit, mocking |

**Porar niyom:** lesson gula ek ek dhap kore lekha, kintu code ta shesh obosthar. Tai purono lesson er file e pore r lesson er kichu line o dekhbe (jemon Lesson 4 er restaurant e Lesson 7 er `is_approved`). Bhoy peo na, protita lesson bole dey kon ongshe mon dite hobe. "Nije koro" te kono change korle sheshe **firiye nio** (`git checkout .`), jate pore r lesson er shathe code mile.

## AI assistant (optional)

Lesson 11 er assistant Claude API use kore. Chalu korte `.env` e `ANTHROPIC_API_KEY=...` dao. Protita proshne ektu taka lage. Key na thakle oi ekta endpoint `503` dey, baki shob kichu chole.

## Script

| Command | Kaj |
|---|---|
| `python -m scripts.seed_demo` | Khali database e demo account ar restaurant |
| `python -m scripts.create_admin` | Notun admin account (API diye admin banano jay na) |
| `python -m scripts.make_order_late ORDER_ID 20` | Demo r jonno: order ta ke "20 minute late" dhorano |

## Folder structure

```
app/
├── main.py           # app shuru hoy ekhan theke
├── core/             # settings (.env), password hash, JWT token
├── db/               # database connection, session
├── models/           # database table (SQLAlchemy)
├── schemas/          # request/response er shape (Pydantic)
├── services/         # byabshar niyom (dam, order er dhap, compensation, recommendation, assistant)
└── api/
    ├── deps.py       # current user, role check
    └── v1/           # endpoint gula
scripts/              # terminal theke chalanor script
tests/                # automatic test
docs/
├── lessons/          # 11 ta lesson
├── project-report.md # diagram, feature, shimabaddhota
└── demo-guide.md     # presentation er golpo
```
