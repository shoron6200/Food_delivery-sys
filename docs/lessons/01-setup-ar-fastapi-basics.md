# Lesson 1: Backend ki, ar FastAPI diye prothom API

Ei lesson er code: `app/main.py`

## 1. Backend ki?

Ekta restaurant er kotha bhabo:

| Restaurant e | Software e | Amader project e |
|---|---|---|
| Customer | **Client** (mobile app, website) | pore banabo; ekhon Swagger page |
| Waiter | **API** (order ney, khabar ene dey) | FastAPI |
| Kitchen | **Server logic** (ashol kaj) | amader Python code |
| Store room | **Database** (shob jinish joma thake) | SQLite |

Customer kokhono kitchen e dhuke na. She waiter ke bole, waiter kitchen theke ene dey.
Thik temni mobile app kokhono database e shorashori hat dey na. She **API ke request pathay**, API **response** dey.

## 2. Request ar Response

Ekta request e 3 ta jinish thake:

1. **Method**: ki korte chai
2. **URL**: kon jinish er upor
3. **Body** (optional): shathe kono data

| Method | Mane | Udahoron |
|---|---|---|
| `GET` | data dekhao | `GET /restaurants` |
| `POST` | notun kichu banao | `POST /auth/register` |
| `PATCH` | ektu change koro | `PATCH /restaurants/5` |
| `DELETE` | muche dao | `DELETE /cart/items/3` |

Response e thake ekta **status code** ar shadharonoto **JSON** data. JSON dekhte Python dict er moto:

```json
{"status": "ok", "app": "Food Delivery API"}
```

Je status code gula amra use korbo:

| Code | Mane |
|---|---|
| `200` | Thik ache |
| `201` | Notun jinish toiri hoyeche |
| `401` | Tumi ke, jani na (login koro) |
| `403` | Tomake chini, kintu eta korar permission nai |
| `404` | Ei jinish nai |
| `409` | Conflict (jemon: ei phone e age thekei account ache) |
| `422` | Tomar pathano data bhul (jemon: phone number 5 digit er) |

## 3. Amader prothom endpoint

`app/main.py` er shesh e eta ache:

```python
@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
```

Line by line:

- `@app.get("/")` ekta **decorator**. Eta FastAPI ke bole: "keu `GET /` request pathale nicher function ta chalao."
- `def health()` shadharon Python function.
- `return {...}` ekta dict return korchi. FastAPI nije theke etake JSON baniye client ke pathay.

Ei rokom ekta function ke bole **endpoint** ba **route**.

## 4. Server chalano

README er step gula follow koro. Shesh command ta:

```bash
uvicorn app.main:app --reload
```

- `uvicorn` holo server program, je request shone ar amader code chalay.
- `app.main:app` mane "`app/main.py` file er bhitorer `app` variable".
- `--reload` dile code save korlei server nije restart ney. Shudhu development e use korbe.

Ekhon browser e:

- http://127.0.0.1:8000/ e gele health response dekhbe
- http://127.0.0.1:8000/docs e gele **Swagger UI** dekhbe

Swagger UI FastAPI nije banay, amader code pore. Okhane protita endpoint er "Try it out" button diye request pathano jay. Varsity te demo dekhanor jonno eta khub kaje lagbe.

## 5. Folder gula keno alada?

Shob code ek file e likhle 500 line er pore kichu khuje pawa jay na. Tai kaj onujayi bhag kora:

| Folder | Ki thake | Lesson |
|---|---|---|
| `core/` | settings, security | 3 |
| `db/` | database connection | 2 |
| `models/` | database table | 2 |
| `schemas/` | request/response er shape | 2 |
| `api/v1/` | endpoint | 3 |

`v1` mane API version 1. Pore boro change korle `v2` banano jay, purono app bhenge jay na.

## 6. Nije koro

1. `app/main.py` te notun endpoint banao: `GET /hello/{name}`, jeta `{"message": "Hello, Rahim"}` return kore.
   Hint:
   ```python
   @app.get("/hello/{name}")
   def hello(name: str):
       ...
   ```
   `{name}` ke bole **path parameter**.
2. Function e `name: str` er jaygay `name: int` likho, tarpor `/hello/rahim` e jao. Ki status code ashlo? Keno?
3. `/docs` e giye dekho tomar notun endpoint nije thekei chole esheche.

Exercise sheshe ei endpoint ta muche dio. Eta shudhu practice er jonno.
