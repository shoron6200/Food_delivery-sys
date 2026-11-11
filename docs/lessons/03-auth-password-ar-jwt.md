# Lesson 3: Register, Login ar JWT Token

Ei lesson er code: `app/core/security.py`, `app/api/deps.py`, `app/api/v1/auth.py`

## 1. Password kivabe rakhbo?

**Kokhono ashol password database e rakha jabe na.** Database churi hole shob user er password fash hoye jabe, ar manush ek password onek jaygay use kore.

Tai amra rakhi **hash**. Hash holo ek-mukhi function:

```
"my-secret-pass"  →  hash  →  "$2b$12$Xk9...Qe"     (shohoj)
"$2b$12$Xk9...Qe" →   ?    →  "my-secret-pass"     (kora jay na)
```

Amra **bcrypt** use korchi, karon:

- Eta **salt** jog kore: ek e password duibar hash korle duita alada result ashe. Tai duijon er password same holeo hash dekhe bojha jay na.
- Eta **ichcha kore dhir**: ekta hash e 0.1-0.3 second lage. User er jonno kichu na, kintu je koti koti password try korte chay tar jonno onek.

Nije dekho (venv chalu rekhe `python` likhe):

```python
from app.core.security import hash_password, verify_password
h1 = hash_password("abc12345")
h2 = hash_password("abc12345")
print(h1 == h2)                        # False (salt alada)
print(verify_password("abc12345", h1)) # True
print(verify_password("wrong", h1))    # False
```

## 2. Login er por server kivabe chine?

HTTP **kichu mone rakhe na**. Protita request notun. Tahole login korar por ki protibar password pathabo? Na.

Login korle server ekta **token** dey. Eta ekta entry pass er moto: porer protita request e pass dekhalei hoy.

Amader token holo **JWT**. Dekhte emon, 3 bhag, dot diye alada:

```
eyJhbGciOi...  .  eyJzdWIiOiIxIi...  .  K3x9fQ2...
   header            payload             signature
```

- **payload**: `{"sub": "1", "exp": 1790000000}`. `sub` = user id, `exp` = kokhon meyad shesh
- **signature**: server tar `SECRET_KEY` diye shoi kore. Keu payload bodlale shoi mile na, token batil

**Khub joruri:** payload **encrypted na**, je keu pore felte pare. Tai token er bhitore kokhono password ba gopon kichu rakhbe na. Signature shudhu nishchit kore je keu eta **bodlay ni**.

Ei jonnoi `SECRET_KEY` code e nai, `.env` file e ache, ar `.env` git e jay na (`.gitignore` dekho). Key fash hole je keu jekono user er token banate parbe.

## 3. Puro flow

```
REGISTER
  client → POST /api/v1/auth/register {name, phone, password}
  server → schema check → password hash → database e save → 201 + user

LOGIN
  client → POST /api/v1/auth/login (phone, password)
  server → phone diye user khoje → password milay → token banay → 200 + token

PROTECTED REQUEST
  client → GET /api/v1/auth/me     Header: "Authorization: Bearer <token>"
  server → token er shoi + meyad check → user id ber kore → user khoje → 200 + user
```

## 4. `Depends`: FastAPI er shobcheye kajer jinish

`/me` endpoint ta matro 2 line:

```python
@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser) -> User:
    return current_user
```

Token check kothay? `CurrentUser` er bhitore (`app/api/deps.py`):

```python
CurrentUser = Annotated[User, Depends(get_current_user)]
```

`Depends(get_current_user)` mane: "ei endpoint chalanor **age** `get_current_user` chalao, tar result amake dao."

Ar `get_current_user` nijeo duita jinish er upor nirbhor kore: token (`oauth2_scheme`) ar database session (`get_db`). FastAPI puro chain ta nije chalay:

```
me  →  get_current_user  →  oauth2_scheme (header theke token ney)
                         →  get_db        (database session dey)
```

Labh: pore **je kono** endpoint e `current_user: CurrentUser` likhlei sheta login chhara cholbe na. Ek line e.

## 5. Code er security decision gula

Egula viva te jiggesh korte pare:

| Decision | Keno |
|---|---|
| Phone bhul hok ba password, error message **ek e** | Alada message dile keu bujhe felbe kon phone e account ache |
| `role` e `admin` dewa jay na (422 ashe) | Na hole je keu nijeke admin baniye felto |
| Duplicate phone database er `unique` rule diye dhori | "Age check, tarpor save" korle duita request ek shathe ashle duitai pass kore jete pare (**race condition**) |
| Token er meyad 60 minute | Token churi holeo kichukkhon por ochol |
| `UserOut` e `password_hash` nai | Bhul koreo hash client er kache jabe na |

## 6. Swagger e try koro

1. `/docs` e jao, `POST /api/v1/auth/register` diye ekta account banao
2. Upore dan dike **Authorize** button e click koro
3. `username` e **phone number**, `password` e password dao (Swagger er form e naam `username`, amra okhane phone pathai)
4. Ekhon `GET /api/v1/auth/me` chalao. Tomar tothyo ashbe
5. Authorize theke **Logout** kore abar `/me` chalao. `401` ashbe

## 7. Test

`tests/test_auth.py` te 13 ta test ache. Chalao:

```bash
python -m pytest -v
```

Test mane code diye code check kora. Notun feature jog korar por test chalale bojha jay purono kichu bhangeni.

## 8. Nije koro

1. Login kore token ta copy koro, tarpor payload pore dekho:
   ```python
   import jwt
   print(jwt.decode("TOMAR_TOKEN", options={"verify_signature": False}))
   ```
   Secret key chharai pora gelo, tai na? Ei jonnoi payload e gopon kichu rakha jay na.
2. `.env` e `ACCESS_TOKEN_EXPIRE_MINUTES=1` likho, server restart koro, login koro, 1 minute por `/me` chalao. Ki holo?
3. `tests/test_auth.py` te notun test lekho: 1 okkhor er `name` diye register korle `422` ashe.
4. Nijer bhashay bolo: `401` ar `403` er parthokko ki? (Porer lesson e `403` lagbe.)
