# Lesson 4: Restaurant, Menu ar Permission

Ei lesson er code: `app/models/restaurant.py`, `app/schemas/restaurant.py`, `app/api/v1/restaurants.py`, `app/api/deps.py` (shesh er `require_role`)

Ei lesson likhar shomoy restaurant e `is_approved`, rating ar `/restaurants/mine` chilo na. Egula Lesson 7 ar 8 e jog hoyeche, tai code e ektu beshi dekhbe. Ekhon shudhu ei lesson er ongshotuku te mon dao.

## 1. Ki banalam

| Endpoint | Kaj | Ke parbe |
|---|---|---|
| `GET /restaurants` | List, `search` diye khoja | shobai |
| `GET /restaurants/{id}` | Ekta restaurant | shobai |
| `GET /restaurants/{id}/menu` | Menu | shobai |
| `POST /restaurants` | Notun restaurant | shudhu vendor |
| `PATCH /restaurants/{id}` | Tothyo bodlano, khola/bondho | shudhu malik |
| `POST /restaurants/{id}/menu-items` | Menu te item jog | shudhu malik |
| `PATCH /menu-items/{id}` | Item bodlano, dam, available on/off | shudhu malik |

Eitai **CRUD**: **C**reate (`POST`), **R**ead (`GET`), **U**pdate (`PATCH`), **D**elete. Delete keno nai, sheta section 9 e.

## 2. Foreign key: table er moddhe shomporko

Ekhon amader 3 ta table, ar tara eke oporer shathe jukto:

```
users (1) ──────< (onek) restaurants (1) ──────< (onek) menu_items
      owner_id                        restaurant_id
```

Ekjon vendor er onek restaurant thakte pare. Ekta restaurant er onek menu item. Eke bole **one-to-many** shomporko. ER diagram e eta lagbe.

```python
owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
```

`ForeignKey("users.id")` mane: "`owner_id` te je number thakbe, sheta obosshoi `users` table er kono ashol `id` hote hobe." Je user nai tar naam e restaurant banano jabe na. Database nije atkay.

**SQLite er ekta fad:** SQLite default e foreign key check **kore na**. Tai `app/db/database.py` te protita connection e `PRAGMA foreign_keys=ON` chalano hoyeche. PostgreSQL e eta lage na.

## 3. `relationship`: Python diye ek table theke arek table e jawa

```python
menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="restaurant", ...)
```

Eta **column na**. Database e `menu_items` name kono column nai. Eta shudhu Python er shubidha:

```python
restaurant.menu_items    # ei restaurant er shob item (list)
item.restaurant          # ei item kon restaurant er
item.restaurant.owner_id # ek line e malik porjonto
```

SQLAlchemy pichone `SELECT * FROM menu_items WHERE restaurant_id = ...` nije chalay. Tai menu endpoint ta ek line:

```python
def read_menu(restaurant: AnyRestaurant):
    return restaurant.menu_items
```

## 4. Dam keno `int`, `float` na?

Python e likhe dekho:

```python
>>> 0.1 + 0.2
0.30000000000000004
```

`float` dashomik shonkha thik thik rakhte pare na. Takar hishab e 1 poysha gormil o bug. Tai amra dam rakhi **purno taka, `int` e** (`price: int`). `99.5` pathale `422` ashbe.

Schema te `Field(gt=0)` ache, mane dam 0 ba minus hote parbe na.

## 5. Query parameter: search, limit, offset

URL er `?` er porer ongsho:

```
GET /api/v1/restaurants?search=kacchi&limit=10&offset=20
```

```python
def list_restaurants(
    db: DbSession,
    search: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
```

Function er je parameter URL path e nai (`{...}` er moddhe nai), FastAPI sheta query parameter dhore ney.

- `search`: naam er moddhe khoje, boro/chhoto hater okkhor na dekhe
- `limit` + `offset`: eke bole **pagination**. 10,000 restaurant ek shathe pathale app dhir hobe, tai ek bar e shorbocho 100. `offset=20` mane prothom 20 ta baad

## 6. Permission: 3 ta proshno

Kono change korar age server 3 ta proshno kore:

| Proshno | Uttor "na" hole |
|---|---|
| 1. Tumi ke? (token ache?) | `401` |
| 2. Tomar role thik? (vendor?) | `403` |
| 3. Jinish ta tomar? (tumi malik?) | `403` |

Ar jinish ta na thakle `404`.

Proshno 2 er code `app/api/deps.py` te:

```python
def require_role(*roles: UserRole):
    def check_role(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, ...)
        return user
    return check_role
```

Eta **function er bhitore function**. `require_role(UserRole.vendor)` call korle she ekta notun function (`check_role`) baniye return kore, je mone rakhe kon role cholbe. Eke bole **closure**. Labh: pore `require_role(UserRole.admin)` ba `require_role(UserRole.rider)` likhlei notun rule toiri.

Proshno 3 er code `check_owner` e:

```python
if restaurant.owner_id != vendor.id:
    raise HTTPException(403, "This is not your restaurant")
```

## 7. `Depends` er chain

Lesson 3 e ekta dependency dekhechi. Ekhon chain ta lomba:

```
OwnRestaurant
  └─ get_own_restaurant
       ├─ Vendor         → require_role → get_current_user → token + db
       └─ AnyRestaurant  → get_restaurant → db   (na pele 404)
```

Tai endpoint e shudhu `restaurant: OwnRestaurant` likhlei 4 ta check hoye jay: token, role, 404, malik.

```python
def create_menu_item(data: MenuItemCreate, restaurant: OwnRestaurant, db: DbSession):
```

## 8. Duita joruri choto jinish

**`owner_id` token theke ashe, body theke na.**

```python
restaurant = Restaurant(**data.model_dump(), owner_id=vendor.id)
```

Client jodi body te `owner_id` pathate parto, tahole she onner naam e restaurant khulte parto. `RestaurantCreate` schema te `owner_id` nei, tai pathaleo baad pore jay. **Niyom: "ke korche" shob shomoy token theke nao.**

**PATCH e shudhu pathano field bodlay.**

```python
for field, value in data.model_dump(exclude_none=True).items():
    setattr(restaurant, field, value)
```

`{"is_open": false}` pathale shudhu `is_open` bodlabe. Update schema te shob field optional (`None`), ar `exclude_none=True` `None` gula baad dey. `setattr(obj, "name", "X")` holo `obj.name = "X"` er e arek rup, jokhon field er naam variable e thake.

## 9. Design decision (viva er jonno)

| Decision | Keno |
|---|---|
| Menu item **delete nai**, `is_available` off kori | Pore order gula menu item ke point korbe. Item muche dile purono order er hishab bhenge jabe |
| `category` alada table na, ekta text column | Shohoj rakhar jonno. Khoroch: ekjon "Biryani" arekjon "biriyani" likhte pare. Boro hole alada `categories` table e nibo (eke bole **normalization**) |
| Menu te bondho item o dekhai, `is_available: false` shoho | App e "ekhon nai" likhe dhushor kore dekhano jay, ar vendor nijer bondho item dekhte pay |
| Role check age, tarpor 404 | Login chhara keu jeno `404` / `403` dekhe bujhte na pare kon id te restaurant ache |

## 10. Swagger e try koro

1. Ekta **vendor** account banao (`role: "vendor"`), Authorize koro
2. `POST /restaurants` diye restaurant banao, `id` ta mone rakho
3. `POST /restaurants/{id}/menu-items` diye 2-3 ta item jog koro
4. Logout kore `GET /restaurants/{id}/menu` chalao. Login chharai dekha jay
5. Ekta **customer** account diye login kore `POST /restaurants` chalao. `403` ashbe

Notun restaurant `GET /restaurants` list e **dekha jabe na** jotokkhon na admin approve kore (Lesson 7). Tar age `GET /restaurants/{id}` ba `GET /restaurants/mine` diye dekho.

## 11. Nije koro

1. `GET /restaurants` e notun query parameter jog koro: `open_only: bool = False`. `true` hole shudhu khola restaurant ashbe.
   Hint: `query = query.where(Restaurant.is_open)`. Tarpor `tests/test_restaurants.py` te er jonno ekta test lekho.
2. `Restaurant` e `phone` column jog koro (model, `RestaurantCreate`, `RestaurantUpdate`, `RestaurantOut`). Server chaliye `GET /restaurants` e jao. Error ashbe. Keno? (Lesson 2, section 5 dekho.)
3. `restaurants.py` te `GET /restaurants/mine` ache (vendor er nijer restaurant gula; Lesson 7 e jog hoyeche). Eta `GET /restaurants/{restaurant_id}` er **upore** lekha.
   Niche niye gele ki hoy try kore dekho, ar bhabo keno. Tarpor firiye rakho. (Uttor Lesson 7, section 4 e.)
4. Nijer bhashay bolo: ekjon customer onner restaurant `PATCH` korte gele `403` pay, ar login chhara gele `401`. Parthokko ta ki?
