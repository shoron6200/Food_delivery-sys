# Demo Guide: presentation e ki dekhabe

Puro golpo ta 8-10 minute e dekhano jay. Ager din **ontoto dui bar** practice koro.

## Age theke prostuti (5 minute)

```bash
# 1. Purono database muche notun demo data
#    (Windows e: del food_delivery.db)
rm -f food_delivery.db
python -m scripts.seed_demo

# 2. Server
uvicorn app.main:app
```

`seed_demo` 4 ta account ar 3 ta approved restaurant banay. Shob account er password: `demo-pass-123`

| Role | Phone |
|---|---|
| admin | `01700000001` |
| vendor | `01700000002` |
| customer | `01700000003` |
| rider | `01700000004` |

**Shobcheye kajer tip:** browser e `http://127.0.0.1:8000/docs` **4 ta alada tab e** kholo. Protita tab e **Authorize** button diye alada role e login koro (username = phone). Swagger er login tab onujayi alada thake, tai bar bar logout korte hoy na. Tab gula ei krome shajao: Customer, Vendor, Rider, Admin.

Arekta terminal khule rakho (project folder e, venv chalu), dhap 6 er jonno.

## Golpo

### 1. Shomossa ta bolo (30 second)

"Food app e 3 ta biroktikor jinish: checkout e dam bere jay, khabar late ashe kintu khotipuron pete jhamela, ar ki khabo thik korte shomoy jay. Amar project ei 3 ta shomadhan kore."

### 2. Honest Price (Customer tab)

1. `GET /restaurants`: 3 ta restaurant
2. `GET /restaurants/1/menu`: Kacchi Ghor er menu
3. `PUT /cart/items/1` e `{"quantity": 2}` (Kacchi Biryani)
4. `PUT /cart/items/4` e `{"quantity": 1}` (Borhani)

Uttor er `price` dekhao: `subtotal 700 + delivery_fee 40 + platform_fee 5 = total 745`.

**Bolo:** "Cart e prothom item dewar shathe shathei puro hishab. Kono lukano charge nai."

5. `POST /orders` e `{"delivery_address": "Flat 4B, Mirpur 10, Dhaka"}`

**Bolo:** "Order er total o 745. Cart ar order ek e function diye hishab kore, tai alada howa shombhob na. Er jonno test o ache." `promised_at` ta dekhao: "ei shomoy er moddhe deyar promise."

### 3. Restaurant (Vendor tab)

1. `GET /orders`: notun order ta
2. `PATCH /orders/1/status` e `{"status": "accepted"}`

**Customer tab e fire** `PATCH /orders/1/status` e `{"status": "cancelled"}` pathao. `409`.

**Bolo:** "Order er dhap ekta state machine. Ranna shuru hole ar cancel kora jay na."

### 4. Rider (Rider tab)

1. `GET /orders/available`: order ta dekha jacche
2. `POST /orders/1/claim`

**Vendor tab:** `PATCH /orders/1/status` e `{"status": "ready"}`

### 5. Role er nirapotta (jekono tab, 30 second)

Customer tab theke `POST /restaurants` chalao. `403`.

**Bolo:** "Protita role shudhu nijer kaj korte pare."

### 6. Late Compensation (terminal + Rider tab)

**Bolo:** "Ekhon dhori rider 35 minute late. 35 minute boshe na theke ekta demo script diye promise er shomoy pichiye dicchi."

Terminal e:

```bash
python -m scripts.make_order_late 1 35
```

**Rider tab:** `PATCH /orders/1/status` e `{"status": "picked_up"}`, tarpor `{"status": "delivered"}`.

Uttor e dekhao: `late_minutes: 35`, `compensation: 110`.

**Customer tab:** `GET /wallet`. Balance 110, karon lekha.

**Bolo:** "Customer kichu koreni. Kono complain na, kono chat na. 30 minute er beshi late, tai delivery fee 40 ar khabar er 10% mane 70, mot 110 taka nije theke wallet e."

### 7. Review (Customer tab)

1. `POST /orders/1/review` e `{"rating": 4, "comment": "Moja, kintu late"}`
2. Abar pathao. `409`
3. `GET /restaurants/1`: `average_rating: 4.0`

**Bolo:** "Shudhu je khabar peyeche shei review dite pare, ek bar. Fake review deya jay na."

### 8. Recommendation (Customer tab)

`GET /recommendations`

**Bolo:** "Biryani kheyechi, tai upore biryani. Protitar pashe karon lekha. Eta rule-based, machine learning na, karon notun app e ML er moto data thake na."

### 9. Wallet diye order (Customer tab)

1. `PUT /cart/items/6` e `{"quantity": 1}` (Beef Burger). `409` ashbe na, karon cart khali
2. `POST /orders` e `{"delivery_address": "Flat 4B, Mirpur 10, Dhaka", "use_wallet": true}`

Dekhao: `total 295`, `wallet_used 110`, `amount_due 185`.

### 10. AI Assistant (Customer tab, jodi API key thake)

`POST /assistant/suggest` e `{"message": "200 takar moddhe halka nasta ar cha, 2 jon"}`

**Bolo:** "Banglish bujhche. Model shudhu item er id bachhe, naam ar dam amar database theke ashe, tai model bhul dam bolte pare na."

Key na thakle `503` dekhiye bolo: "Bairer service na thakleo baki app chole."

### 11. Admin (Admin tab, 30 second)

1. `GET /orders`: shob order
2. `GET /admin/restaurants`: shob restaurant

### 12. Test (terminal, 20 second)

```bash
python -m pytest -q
```

**Bolo:** "155 ta automatic test. Notun kichu jog korle bojha jay purono kichu bhangeni."

## Jodi kichu bhul hoy

| Shomossa | Shomadhan |
|---|---|
| `401` | Token er meyad shesh (60 minute). Oi tab e abar Authorize |
| Shob elomelo | `rm -f food_delivery.db`, `python -m scripts.seed_demo`, server restart, 4 tab e abar Authorize |
| `make_order_late` bole "already delivered" | Deliver korar **age** chalate hobe |
| Rider `claim` e `409` | Order `accepted` hoyeche? Rider er hate onno delivery ache? |
| Internet nai | AI assistant chhara shob chole. Dhap 10 baad dao |

## Shombhabbo proshno

Protita lesson er sheshe "Viva proshno" ache. Shobcheye beshi asha gula:

1. Password kivabe rakho? (Lesson 3)
2. JWT ki? Payload ki gopon? (Lesson 3)
3. `401` ar `403` er parthokko? (Lesson 4)
4. Taka `float` e rakho ni keno? (Lesson 4)
5. Cart e dam save koro na, order e koro, keno? (Lesson 5, 6)
6. Transaction / ACID ki? (Lesson 6)
7. Race condition ki? Ekta udahoron dao (Lesson 6, 7)
8. Wallet e balance column nai keno? (Lesson 9)
9. Tomar recommendation ki AI? (Lesson 10: shot uttor dao)
10. LLM bhul bolle ki hoy? (Lesson 11)

Shimabaddhota r talika `docs/project-report.md` er section 11 te. Nije theke bolle bhalo dekhay.
