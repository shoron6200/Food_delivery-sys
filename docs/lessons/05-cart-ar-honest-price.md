# Lesson 5: Cart ar Honest Price

Ei lesson er code: `app/services/pricing.py`, `app/models/cart.py`, `app/schemas/cart.py`, `app/api/v1/cart.py`

Eta amader **prothom unique feature**. Onno app e checkout e giye total bere jay. Amader app e cart e prothom item dewar shathe shathe puro hishab dekha jay, ar order e thik oi taka i kata hobe.

## 1. Ki banalam

| Endpoint | Kaj |
|---|---|
| `GET /cart` | Cart + dam er puro breakdown |
| `PUT /cart/items/{menu_item_id}` | Item rakho, quantity eto (body: `{"quantity": 2}`) |
| `DELETE /cart/items/{menu_item_id}` | Ekta item shorao |
| `DELETE /cart` | Puro cart khali koro |

Shudhu **customer** cart use korte pare. Protita uttor e emon breakdown ashe:

```json
{
  "restaurant": {"id": 1, "name": "Kacchi Ghor", "is_open": true},
  "items": [
    {"menu_item_id": 1, "name": "Kacchi Biryani", "unit_price": 320,
     "quantity": 2, "line_total": 640, "is_available": true}
  ],
  "price": {"subtotal": 640, "delivery_fee": 40, "platform_fee": 5, "total": 685}
}
```

## 2. Honest Price: promise ta code e kivabe rakha hoy

Promise 3 ta, ar protitar pichone ekta code decision:

| Promise | Code e |
|---|---|
| Dokaner dam = app er dam | `unit_price` shorashori `menu_items.price` theke ashe. Majhkhane kono markup er jayga nai |
| Kono lukano charge nai | Fee duitai (`delivery_fee`, `platform_fee`) alada kore dekhano, ar `subtotal + fee = total` test diye check kora |
| Ja dekhbe tai dibe | Cart ar order (Step 6) **ek e function** `calculate_price` call korbe |

Shesh er ta shobcheye joruri. Cart er hishab ek jaygay ar order er hishab arek jaygay likhle ekdin duita alada hoye jabe, ar customer dekhbe 685 kintu kata hobe 700. Hishab **ek jaygay** thakle sheta hote pare na.

## 3. Business logic ar `services/` folder

Ekhon porjonto shob code router e chilo. Ebar notun folder: `app/services/`.

| | Router (`api/v1/`) | Service (`services/`) |
|---|---|---|
| Proshno | Ke request korlo? Data thik? Kon status code? | Byabshar niyom ki? Koto taka? |
| Jane | HTTP, token, database | Shudhu shonkha |

`app/services/pricing.py` er main function:

```python
def calculate_price(lines: list[tuple[int, int]]) -> PriceBreakdown:
    subtotal = sum(unit_price * quantity for unit_price, quantity in lines)
    if subtotal == 0:
        return PriceBreakdown(subtotal=0, delivery_fee=0, platform_fee=0, total=0)
    return PriceBreakdown(
        subtotal=subtotal,
        delivery_fee=DELIVERY_FEE,
        platform_fee=PLATFORM_FEE,
        total=subtotal + DELIVERY_FEE + PLATFORM_FEE,
    )
```

Eta ekta **pure function**: input `[(320, 2), (60, 1)]` dile shob shomoy ek e output. Database chhoy na, HTTP jane na. Tin ta labh:

1. **Abar use kora jay.** Step 6 e order o eta call korbe
2. **Test kora shohoj.** Server ba database lage na
3. **Ek jaygay bodlalei hoy.** Kal delivery fee 50 hole shudhu `DELIVERY_FEE = 50`

`PriceBreakdown` holo `@dataclass(frozen=True)`. Dataclass mane shudhu data rakhar chhoto class, `__init__` nije likhte hoy na. `frozen=True` mane banano r por bodlano jay na, tai hishab bhul kore keu pore change korte parbe na.

## 4. Unit test vs API test

Ekhon duirokom test ache:

| | Unit test | API test |
|---|---|---|
| File | `tests/test_pricing.py` | `tests/test_cart.py` |
| Ki check kore | Ekta function, eka | Puro rasta: request → router → database → response |
| Lage | Kichu na | Test server + test database |

```python
def test_subtotal_is_price_times_quantity():
    price = calculate_price([(320, 2), (60, 1)])
    assert price.subtotal == 700
```

Niyom: hishab-nikash er jonno unit test, "puro jinish ta jora lege kaj kore to?" er jonno API test.

## 5. Cart e dam rakhi na

`cart_items` table e matro 3 ta column: `user_id`, `menu_item_id`, `quantity`. **Dam nai.**

Protibar `GET /cart` e dam menu theke notun kore pora hoy (`build_cart` function). Tai vendor dam bodlale customer er cart e shathe shathe notun dam dekha jay. Purono dam dekhiye pore beshi nile sheta "honest" hoto na.

Er jonno test ache: `test_cart_uses_the_menu_price_of_right_now`.

Order e ulto hobe: order hoye gele dam **jome jabe** (snapshot), karon bikri hoye jawa jinish er dam ar bodlay na. Sheta Step 6.

## 6. Composite primary key

```python
user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), primary_key=True)
```

Ekhane alada `id` column nai. **Duita column mile** primary key. Mane (user 5, item 12) jora ta table e ek bar i thakte parbe. Ek e biryani duibar nile notun row hoy na, `quantity` bare.

Khojar shomoy jora ta dite hoy:

```python
db.get(CartItem, (customer.id, menu_item_id))
```

## 7. `PUT` keno, `POST` na?

| | `POST` | `PUT` |
|---|---|---|
| Mane | "Notun ekta banao" | "Eta **emon** kore dao" |
| 3 bar pathale | 3 ta jinish | 1 ta jinish, ek e obostha |

`PUT /cart/items/1 {"quantity": 2}` mane "item 1 er quantity 2 hok". Net kharap, app ek e request 3 bar pathalo, tao quantity 2 i thakbe, 6 hobe na. Emon request ke bole **idempotent**.

Ek e karone `DELETE /cart/items/1` item na thakleo error dey na. "Item ta jeno na thake" chaoya hoyechilo, ar sheta nai.

## 8. `409 Conflict`

Tin jaygay `409` dei:

- Item ta ekhon available na
- Restaurant bondho
- Cart e onno restaurant er item ache

`422` er shathe parthokko: `422` mane **data tai bhul** (quantity 0). `409` mane data thik, kintu **ekhonkar obosthar shathe mile na**. Kal restaurant khulle ek e request pass korbe.

Ek cart e ek restaurant keno? Karon ekta order ekta restaurant theke ekjon rider ane. Duita restaurant mane duita order.

## 9. Swagger e try koro

1. Shohoj upay: `python -m scripts.seed_demo` chalao (khali database e). Eta approved restaurant, menu ar 4 ta account baniye dey; password `demo-pass-123`, phone gula terminal e dekhabe.
   Karon: approve na kora restaurant theke cart e kichu newa jay na (Lesson 7)
2. **Customer** account diye Authorize koro
3. `PUT /cart/items/{menu_item_id}` e `{"quantity": 2}` pathao. `price` ongsho ta dekho
4. Ek e request abar pathao. Total bodlalo?
5. Vendor diye item er dam bodlao, tarpor customer diye `GET /cart` dekho

## 10. Nije koro

1. **Free delivery:** niyom banao, `subtotal` 500 taka ba beshi hole `delivery_fee` 0.
   Age `tests/test_pricing.py` te 2 ta test lekho (499 takay fee ache, 500 takay nai), dekho fail kore. Tarpor `pricing.py` thik koro.
   Kheyal koro: `cart.py` te **ek line o** hat dite hoy ni, tao cart e notun niyom chole esheche. Eitai services layer er labh.
   Onno file er kichu test o ekhon fail korbe (jara 500 takar beshi order e 40 taka fee asha kore). Sheta thik: niyom bodlale purono test jane na. Dekhe niye change ta **firiye nio**, pore r lesson 40 taka dhore lekha.
2. Ek bar e shorbocho 20 ta item newa jay. Ei niyom kon file e? 10 korte chaile ki bodlabe?
3. `CartOut` e `item_count` field jog koro (shob quantity er jogfol). Schema ar `build_cart` duitai bodlate hobe.
4. Viva proshno, nijer bhashay uttor dao:
   - Cart e dam save kori na keno?
   - `PUT` ke idempotent bola hoy keno?
   - `409` ar `422` er parthokko ki?

Test ekhon druto chole (2-3 second), karon `tests/conftest.py` te `BCRYPT_ROUNDS=4` dewa. Ashol server e eta 12 i thake.
