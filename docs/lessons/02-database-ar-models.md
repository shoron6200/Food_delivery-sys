# Lesson 2: Database, Model ar Schema

Ei lesson er code: `app/db/database.py`, `app/models/user.py`, `app/schemas/user.py`

## 1. Database keno?

Python variable e data rakhle server bondho korlei shob muche jay. Database data ke **disk e** rakhe.

Amra **relational database** use korchi. Ete data thake **table** e:

| id | name | phone | role |
|---|---|---|---|
| 1 | Rahim | 01712345678 | customer |
| 2 | Karim | 01812345678 | vendor |

- Protita **row** ekta user
- Protita **column** ekta tothyo (name, phone...)

Ekhon amra **SQLite** use korchi. Eta ekta file (`food_delivery.db`), alada kichu install korte hoy na.
Pore **PostgreSQL** e jabo. Tokhon shudhu `.env` e `DATABASE_URL` bodlalei hobe, karon amra SQLAlchemy use korchi.

## 2. ORM: class diye table

Database er bhasha holo SQL (`SELECT * FROM users WHERE phone = '017...'`).
**ORM** (SQLAlchemy) amader Python class likhte dey, SQL she nije baniye ney.

> **class = table, object = row, attribute = column**

`app/models/user.py`:

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.customer)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

| Likha | Mane |
|---|---|
| `primary_key=True` | Protita row er alada number (1, 2, 3...). Database nije dey |
| `unique=True` | Ek phone number e duita account hobe na. Database nije atkabe |
| `index=True` | Phone diye khoja druto hobe (boi er shuchipotro er moto) |
| `default=...` | Kichu na dile ei value boshbe |
| `Enum(UserRole)` | Shudhu 4 ta value e cholbe: customer, vendor, rider, admin |
| `password_hash` | Ashol password na, tar hash (Lesson 3) |

## 3. Session: database er shathe kotha bola

`app/db/database.py` te 3 ta jinish ache:

- **engine**: database er shathe connection
- **SessionLocal**: session banay. Session holo ekta "khata", jekhane tumi change gula lekho
- **get_db**: protita request er jonno ekta session khole, kaj sheshe bondho kore

```python
def get_db():
    db = SessionLocal()
    try:
        yield db        # endpoint ke session ta dey
    finally:
        db.close()      # endpoint shesh hole (error holeo) bondho kore
```

Data save korar niyom:

```python
db.add(user)     # khatay likhlam (ekhono database e jay ni)
db.commit()      # ekhon database e pakka holo
db.rollback()    # bhul hole khatar lekha baad
```

## 4. Model vs Schema (shobcheye beshi confusion ekhane)

Duita alada jinish, duitai class:

| | Model (`models/`) | Schema (`schemas/`) |
|---|---|---|
| Library | SQLAlchemy | Pydantic |
| Kaj | Database table er shape | Request / response er shape |
| Udahoron | `User` | `UserCreate`, `UserOut` |

Alada keno? Karon database e ja ache tar shob client ke dewa jay na:

- `UserCreate` e `password` ache (client pathay), kintu `id` nai (database dey)
- `UserOut` e `id` ache, kintu `password_hash` **nai**. Tai bhul koreo password hash baire jabe na

Schema data **check** o kore:

```python
phone: str = Field(pattern=r"^01[3-9]\d{8}$")
password: str = Field(min_length=8)
```

Keu 5 digit er phone pathale FastAPI nije theke `422` error dey. Amader kono `if` likhte hoy ni.

## 5. Table kokhon toiri hoy?

`app/main.py` te server chalu howar shomoy:

```python
Base.metadata.create_all(bind=engine)
```

Eta je table gula nai shegula banay.

**Mone rekho:** `create_all` purono table **change kore na**. Model e notun column jog korle development e `food_delivery.db` file ta muche abar server chalao. Pore **Alembic** shikhbo, jeta data na muche table change korte pare.

## 6. Nije koro

1. Server chaliye `/docs` theke ekta user register koro.
2. Database er bhitore dekho:
   ```bash
   python -c "import sqlite3; print(sqlite3.connect('food_delivery.db').execute('SELECT * FROM users').fetchall())"
   ```
   `password_hash` column e ki dekhcho? Tomar ashol password ki okhane ache?
3. Ektu graphical dekhte chaile "DB Browser for SQLite" install kore file ta kholo.
4. Bhabo: `phone` e `unique=True` na thakle ki shomossa hoto?
