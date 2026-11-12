# Lesson 6: Order ar Status Flow

Ei lesson er code: `app/models/order.py`, `app/services/orders.py`, `app/schemas/order.py`, `app/api/v1/orders.py`, `app/db/types.py`

Ei step er por ekta order **shuru theke restaurant er "ready" porjonto** API diye kora jay. Rider er ongsho Lesson 7 e.

## 1. Ki banalam

| Endpoint | Kaj | Ke parbe |
|---|---|---|
| `POST /orders` | Cart theke order banay | customer |
| `GET /orders` | "Amar" order gula, notun age | je login kora |
| `GET /orders/{id}` | Ekta order | je oi order er shathe jukto |
| `PATCH /orders/{id}/status` | Order ke porer dhape ney | dhap onujayi |

`GET /orders` e "amar" er mane role onujayi alada: customer er nijer order, vendor er nijer restaurant er order, rider er nijer delivery, admin er shob.

## 2. Order er jibon: state machine

Ekta order er obostha (status) jekono dik e jete pare na. Shudhu ei rasta gula khola:

```
placed ──► accepted ──► ready ──► picked_up ──► delivered
   │        (vendor)   (vendor)    (rider)       (rider)
   ├──► rejected   (vendor)
   └──► cancelled  (customer)
```

Emon "kon obostha theke kon obosthay jawa jay" er niyom ke bole **state machine**. Puro niyom ta `app/services/orders.py` te ekta dict:

```python
TRANSITIONS = {
    (OrderStatus.placed, OrderStatus.accepted): UserRole.vendor,
    (OrderStatus.placed, OrderStatus.rejected): UserRole.vendor,
    (OrderStatus.placed, OrderStatus.cancelled): UserRole.customer,
    (OrderStatus.accepted, OrderStatus.ready): UserRole.vendor,
    (OrderStatus.ready, OrderStatus.picked_up): UserRole.rider,
    (OrderStatus.picked_up, OrderStatus.delivered): UserRole.rider,
}
```

Key holo `(kotha theke, kothay)`, value holo **ke** eta korte pare. Table e ja nai ta oshombhob.

Onek `if status == ... and role == ...` likhle 6 ta niyom 30 line e chhoriye jeto, ar ekta bhule gelei bug. Table e likhle ek nojore puro niyom dekha jay, ar notun dhap jog kora mane ek line.

Router e duirokom "na" ache:

| Obostha | Code | Udahoron |
|---|---|---|
| Rasta tai nai | `409` | `placed` theke shorashori `delivered` |
| Rasta ache, kintu tumi oi role na | `403` | customer `accepted` korte chay |

## 3. Snapshot: order e dam jome jay

Lesson 5 e cart e dam rakhi ni, protibar menu theke porechi. Order e **ulto**:

```python
OrderItem(
    menu_item_id=cart_item.menu_item_id,
    name=cart_item.menu_item.name,          # copy
    unit_price=cart_item.menu_item.price,   # copy
    quantity=cart_item.quantity,
)
```

Naam ar dam **copy kore** `order_items` e rakha hoy, ar total 4 ta shonkha (`subtotal`, `delivery_fee`, `platform_fee`, `total`) `orders` e. Karon bikri hoye geche. Kal vendor biryani r dam 320 theke 400 korle gotokaler order e 320 i thakte hobe, na hole hishab mile na.

| | Cart | Order |
|---|---|---|
| Dam kothay | Menu theke, protibar notun | Order er bhitore, jome thaka |
| Keno | Ekhono kine ni, tai ekhonkar dam | Kena shesh, tai tokhonkar dam |

Test: `test_old_order_keeps_its_price_and_name_after_menu_changes`.

Ar Honest Price er promise ta ekhane purno holo. `place_order` thik shei `calculate_price` function call kore ja cart kore. Test: `test_order_charges_exactly_what_the_cart_showed`.

## 4. Transaction: shob hobe, na hoy kichui na

Order place korte 3 ta kaj:

1. `orders` e ekta row
2. `order_items` e koyekta row
3. `cart_items` theke shob muche fela

Dhoro 2 er por server bondho hoye gelo. Tahole order hoyeche kintu cart o bhora, customer abar order korbe. Tai tin ta kaj **ek shathe** hote hobe:

```python
db.add(order)                 # 1 + 2 (order.items shoho)
for cart_item in cart_items:
    db.delete(cart_item)      # 3
db.commit()                   # ekhane shob ek shathe pakka hoy
```

`commit` er age porjonto shob "khatay lekha" (Lesson 2). Ek `commit` = ek **transaction**. Majhpothe bhul hole kichui save hoy na. Database er ei gun ke bole **atomicity** (ACID er A). Viva te ACID jiggesh korle ei udahoron dio.

## 5. Race condition: duijon ek shathe

Dhoro thik ek e muhurte:

- Customer "cancel" chaplo
- Vendor "accept" chaplo

Duita request i pore dekhlo status `placed`, duitai bhablo "thik ache, bodlano jay". Shadharon `order.status = ...` likhle je pore save kore tar ta thake, ar ekjon bhul jane.

Tai `save_status` function e bodlanor shomoy **abar check** hoy, ek e SQL e:

```python
update(Order)
    .where(Order.id == order.id, Order.status == order.status)   # ekhono age r status e ache?
    .values(status=new_status)
```

SQL e: `UPDATE orders SET status='cancelled' WHERE id=5 AND status='placed'`.

Vendor age pouchale status `accepted` hoye geche, tai customer er `WHERE` kono row pay na (`rowcount` 0), ar she `409` pay: "order ta ei matro bodleche". "Check" ar "bodlano" ek dhape hole majhkhane keu dhukte pare na. Lesson 3 er duplicate phone o ek e dhoroner shomossa chilo.

## 6. `404` na `403`?

Lesson 4 e onner restaurant bodlate gele `403` diyechi. Ekhane onner order dekhte gele **`404`**:

```python
if order is None or not is_participant(order, user):
    raise HTTPException(404, "Order not found")
```

Parthokko: restaurant **public**, shobai jane 5 number restaurant ache. Order **gopon**. `403` dile bojha jeto "17 number order ache, kintu tomar na". `404` dile bahirer keu jantei pare na kon number ashol.

## 7. Shomoy: `promised_at` ar UTC

Order er shomoy amra ekta **promise** likhe rakhi:

```python
promised_at = ekhon + restaurant.avg_prep_minutes + DELIVERY_MINUTES (20)
```

Eta Lesson 9 e (Late Compensation) kaje lagbe: asholei late holo kina eta diye mapa hobe.

Shob shomoy **UTC** te rakha hoy (`datetime.now(timezone.utc)`), ar uttor e `Z` diye ashe: `"2026-11-11T23:24:10Z"`. Server Dhaka te na Singapore e, tate kichu jay ashe na. App dekhano r shomoy user er local time e bodle ney.

`app/db/types.py` er `UtcDateTime` ekta chhoto column type, karon SQLite timezone mone rakhe na. Eta chhara Dhaka r app UTC shomoy ke local bhebe 6 ghonta bhul dekhato.

## 8. Swagger e try koro

1. `python -m scripts.seed_demo` er account gula use koro (Lesson 5, section 9). Customer diye cart e item dao
2. Customer: `POST /orders` e `delivery_address` dao. `price` ta cart er shathe milao
3. Customer: `GET /cart`. Khali?
4. Vendor diye Authorize: `GET /orders`, tarpor `PATCH /orders/{id}/status` e `{"status": "accepted"}`
5. Customer diye `{"status": "cancelled"}` pathao. `409` ashbe
6. Vendor: `{"status": "delivered"}` pathao. `409`. Tarpor `{"status": "ready"}`

## 9. Nije koro

1. Notun niyom: customer `accepted` obosthateo cancel korte parbe (ranna shuru hoyeche, tao). Koyta line bodlate holo? Kon test ekhon fail kore, ar keno sheta thik?
   Kaj sheshe change ta **firiye nio**, pore r lesson purono niyom dhore lekha.
2. `tests/test_order_rules.py` te ekta test lekho: `picked_up` theke `ready` te fera jay na.
3. `OrderOut` e `item_count` jog koro (shob quantity er jogfol). Hint: `OrderItemOut` er `line_total` jevabe `computed_field` diye kora.
4. Viva proshno:
   - State machine ki? Table (dict) diye likhle ki labh?
   - Order e dam copy kori keno, cart e kori na keno?
   - Transaction ki? Order place e na thakle ki bipod?
   - `WHERE status = 'placed'` na dile ki hote parto?
