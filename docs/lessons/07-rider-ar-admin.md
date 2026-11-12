# Lesson 7: Rider ar Admin

Ei lesson er code: `app/api/v1/admin.py`, `app/api/v1/orders.py` (`/available`, `/claim`), `app/api/v1/restaurants.py` (`/mine`), `scripts/create_admin.py`

Ei step er por **4 ta role i kaj kore**, ar ekta order restaurant theke customer er dorja porjonto jay.

Ei step e table e notun column jog hoyechilo. Tumi shesh obosthar code chalale database e shob age thekei ache, kichu muchte hobe na.

## 1. Ki banalam

| Endpoint | Kaj | Ke |
|---|---|---|
| `GET /orders/available` | Je order e rider lagbe | rider |
| `POST /orders/{id}/claim` | "Ei delivery ami nilam" | rider |
| `PATCH /orders/{id}/status` | `picked_up`, `delivered` | je rider niyeche |
| `GET /restaurants/mine` | Nijer restaurant gula | vendor |
| `GET /admin/restaurants?approved=false` | Approval er opekkhay | admin |
| `PATCH /admin/restaurants/{id}` | Approve / batil | admin |

## 2. Admin kivabe toiri hoy?

Lesson 3 e bolechilam API diye keu admin hote pare na (`role: "admin"` dile `422`). Tahole prothom admin ashbe kotha theke?

```bash
python -m scripts.create_admin
```

Ei script shorashori database e admin banay. Eta chalate hole **server er computer e dhukte** hoy, internet theke kora jay na. Je server e dhukte pare she emnitei malik, tai eta nirapod.

Script ta `UserCreate` schema diyei naam, phone, password check kore. Ek e niyom dui jaygay likhte hoy ni.

## 3. Restaurant approval

Age je kono vendor restaurant khullei sheta list e chole ashto. Ekhon:

```python
is_approved: Mapped[bool] = mapped_column(default=False)
```

| Ki | Approve er age | Pore |
|---|---|---|
| Public list (`GET /restaurants`) | dekha jay na | dekha jay |
| Vendor er nijer list (`/restaurants/mine`) | dekha jay | dekha jay |
| Menu banano | kora jay | kora jay |
| Cart e newa, order kora | `409` | kora jay |

Vendor age menu shajay, admin dekhe approve kore, tarpor customer pay. Eta plan er "verified kitchen" er prothom dhap.

**Vendor nije approve korte pare na keno?** `RestaurantUpdate` schema te `is_approved` field tai nai. Vendor `{"is_approved": true}` pathale Pydantic sheta fele dey. Lesson 4 er `owner_id` er moto ek e buddhi: **je field client er bodlano uchit na, sheta schema tei rekho na.** Test: `test_vendor_cannot_approve_own_restaurant`.

"Order newa jabe kina" check ta cart ar order dui jaygay lage, tai sheta ekta function e (`check_taking_orders`, `app/api/deps.py`).

## 4. Route er kromo: `/mine` keno upore

Lesson 4 er challenge er uttor ekhane. `restaurants.py` te `/restaurants/mine` lekha ache `/restaurants/{restaurant_id}` er **upore**.

FastAPI route gula **upor theke niche** milay. `/restaurants/mine` request ele:

- `{restaurant_id}` age thakle: "mine" ke id bhabe, `int` banate giye fail, `422`
- `/mine` age thakle: thik jaygay jay

Ek e karone `orders.py` te `/available` ache `/{order_id}` er upore. **Niyom: nirdishto path age, `{variable}` path pore.**

## 5. Rider er kaj

```
restaurant accept korlo ──► order "available" list e ashe
rider claim korlo        ──► order.rider_id = rider
restaurant ready korlo
rider picked_up ──► delivered
```

Rider `accepted` obosthatei claim korte pare, jate ranna shesh howar age i she restaurant e pouche jay. Kintu `picked_up` korte pare shudhu `ready` howar por (Lesson 6 er table).

### Duijon rider ek shathe claim korle?

Lesson 6 er race condition abar. Ebar o "check" ar "bodlano" ek SQL e:

```python
update(Order)
    .where(
        Order.id == order_id,
        Order.rider_id.is_(None),                 # ekhono keu ney ni?
        Order.status.in_(WAITING_FOR_RIDER),
    )
    .values(rider_id=rider.id)
```

Je age pouchay she pay (`rowcount` 1). Porer jon er `WHERE` kichu pay na, `409`. Test: `test_only_one_rider_gets_the_order`.

### Ek shomoy ekta delivery

Claim er age check hoy rider er hate age r kono delivery ache kina. Thakle `409`: "age oita shesh koro". Na hole ekjon 10 ta order niye boshe thakto ar khabar thanda hoto.

### Ke ki dekhe

Rider shudhu **nijer newa** order er detail dekhe. Onno rider er order e `404` (Lesson 6, section 6).

## 6. Admin ar order

Admin `GET /orders` e **shob** order dekhe (`list_my_orders` e admin er jonno kono filter nai). Kintu status bodlate pare na: `TRANSITIONS` table e admin er naam kothao nai, tai `403`.

Eta ichchakrito. Admin dekhbe, kintu ranna ba delivery r dhap tar kaj na. **Jar jotatuku dorkar, totatuku khomota.** Eke bole *principle of least privilege*, viva te kaje lagbe.

## 7. Swagger e try koro (puro golpo)

4 ta account lagbe. `/docs` er Authorize diye bar bar bodlate hobe.

1. Terminal e: `python -m scripts.create_admin`
2. **Vendor:** register, restaurant + 2 ta menu item. `GET /restaurants/mine` e `is_approved: false`
3. Logout kore `GET /restaurants`. Khali
4. **Admin:** `GET /admin/restaurants?approved=false`, tarpor `PATCH /admin/restaurants/{id}` e `{"is_approved": true}`
5. **Customer:** cart e item, `POST /orders`
6. **Vendor:** status `accepted`
7. **Rider:** register (`role: "rider"`), `GET /orders/available`, `POST /orders/{id}/claim`
8. **Vendor:** status `ready`
9. **Rider:** status `picked_up`, tarpor `delivered`
10. **Customer:** `GET /orders/{id}`. `delivered`, ar `delivered_at` e shomoy

Eitai tomar varsity demo r mul golpo.

## 8. Nije koro

1. `/admin/users` endpoint banao: admin shob user er list dekhbe (`UserOut` diye). `role` diye filter jog koro.
2. `orders.py` te `/available` route ta `/{order_id}` er niche niye jao, tarpor rider diye `GET /orders/available` chalao. Ki holo? Firiye rakho.
3. Bhabo: rider claim korar por jodi ar na ashe? Ekhon order ta atke thakbe. Ki niyom banale thik hoy? (Shudhu uttor bhabo. Hint: "unclaim" endpoint, ba admin ke rider shoranor khomota.)
4. Viva proshno:
   - Admin API diye banano jay na keno? Tahole kivabe banai?
   - `is_approved` vendor nije `true` korte pare na, eta kon jaygay atkano?
   - Least privilege ki? Ei project e ekta udahoron dao.
