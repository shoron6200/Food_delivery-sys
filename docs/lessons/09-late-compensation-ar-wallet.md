# Lesson 9: Late Compensation ar Wallet

Ei lesson er code: `app/services/compensation.py`, `app/models/wallet.py`, `app/services/wallet.py`, `app/api/v1/wallet.py`, `app/api/v1/orders.py` (`place_order`, `change_status`), `scripts/make_order_late.py`

Eta amader **dwitiyo unique feature**. Onno app e khabar late hole support e chat kore, chobi diye, torko kore taka ferot nite hoy. Amader app e: **late holei wallet e taka, kichu bolte hoy na.**

Ei step e table e notun column jog hoyechilo. Tumi shesh obosthar code chalale database e shob age thekei ache, kichu muchte hobe na.

## 1. Ki banalam

| Ki | Kothay |
|---|---|
| Late hole nije theke wallet credit | rider `delivered` korar muhurte |
| `GET /wallet` | balance + lenden er itihash (customer) |
| Wallet er taka diye porer order e dam kom | `POST /orders` e `"use_wallet": true` |
| Order batil hole khoroch kora credit ferot | `cancelled` / `rejected` e |

Order er uttor e 4 ta notun field: `late_minutes`, `compensation`, `wallet_used`, `amount_due` (rider ke hate koto dite hobe).

## 2. Niyom ta

Lesson 6 e protita order e `promised_at` likhe rekhechilam. Ekhon sheta kaje lagche:

| Koto late | Customer pay |
|---|---|
| 0-15 minute | kichu na (rastay ektu deri hotei pare) |
| 16-30 minute | delivery fee ferot (40 taka) |
| 30 minute er beshi | delivery fee + khabar er dam er 10% |

Puro niyom `app/services/compensation.py` te, duita pure function:

```python
def minutes_late(promised_at, delivered_at) -> int:
    seconds = (delivered_at - promised_at).total_seconds()
    return max(0, int(seconds // 60))

def calculate_compensation(late: int, price: PriceBreakdown) -> int:
    if late <= GRACE_MINUTES:
        return 0
    if late <= BIG_DELAY_MINUTES:
        return price.delivery_fee
    return price.delivery_fee + price.subtotal // 10
```

- Duita `datetime` biyog korle `timedelta` pawa jay. `.total_seconds()` diye second
- `// 60` mane purno minute, bhognangsho baad (20 min 59 sec = 20 min)
- `max(0, ...)` mane age pouchale minus na, 0
- `subtotal // 10` mane 10%, purno takay (Lesson 4: taka shob shomoy `int`)

Lesson 5 er `calculate_price` er motoi: database nai, HTTP nai, tai `tests/test_compensation.py` te shima gula (15, 16, 30, 31) shohoje test kora geche. **Shima r dui pasher shonkha test kora** ke bole *boundary testing*.

## 3. Kokhon chole?

`change_status` e, rider jokhon `delivered` pathay:

```python
if data.status == OrderStatus.delivered:
    now = datetime.now(timezone.utc)
    late = minutes_late(order.promised_at, now)
    compensation = calculate_compensation(late, order.price)
    changes = {"delivered_at": now, "compensation": compensation}
    if compensation > 0:
        db.add(WalletTransaction(user_id=order.customer_id, amount=compensation, ...))
save_status(db, order, data.status, **changes)
```

Status bodlano ar wallet e taka dhoka **ek e transaction e** (Lesson 6). "Delivered holo kintu taka dhuklo na", ba ulto, hote pare na.

Kheyal koro: customer kichu koreni. Kono "claim" endpoint nai. Eitai feature.

## 4. Wallet: balance column nai

`users` table e `wallet_balance` name kono column **nai**. Ache shudhu `wallet_transactions` table:

| id | user_id | order_id | amount | reason |
|---|---|---|---|---|
| 1 | 5 | 12 | +40 | Order #12 arrived 20 minutes late. Sorry! |
| 2 | 5 | 13 | -40 | Paid for order #13 |
| 3 | 5 | 13 | +40 | Refund for order #13 |

Balance = shob `amount` er **jogfol** (Lesson 8 er `SUM`):

```python
select(func.coalesce(func.sum(WalletTransaction.amount), 0))
```

`coalesce(..., 0)` mane: kono row na thakle `SUM` dey `NULL`, tokhon 0 dhoro.

Ei dhoroner table ke bole **ledger** (khatiyan). Niyom: **line shudhu jog hoy, kokhono bodlay na, mochha hoy na.** Bank o evabei hishab rakhe.

Lesson 8 e rating er cholti hishab **save** korechilam, ekhane balance save **kori ni**. Keno ulto?

| | Rating | Wallet |
|---|---|---|
| Koto bar pora hoy | onek (protita list e) | kom (nijer wallet) |
| Ektu bhul hole | 4.3 er jaygay 4.2, khoti nai | karo taka hariye gelo |
| Tai | druto pora age | **nirbhul howa age**, ar protita takar itihash thaka |

Ek e proshno, obostha bhede alada uttor. Viva te eta bolte parle bhalo.

## 5. Credit khoroch kora

```python
if data.use_wallet:
    db.execute(select(User.id).where(User.id == customer.id).with_for_update())
    db.flush()
    order.wallet_used = min(get_balance(db, customer.id), price.total)
    if order.wallet_used > 0:
        db.add(WalletTransaction(..., amount=-order.wallet_used, ...))
```

- `min(balance, total)`: wallet e 5000 thakleo 105 takar bill e 105 i kate
- Khoroch mane **minus** amount er ekta notun line. Purono line e hat dewa hoy na
- `db.flush()`: order ta database e pathay (ekhono pakka na), jate `order.id` pawa jay
- `amount_due = total - wallet_used`: rider ke hate eta dite hobe

**Ek taka dui bar khoroch (double spend):** customer jodi ek e muhurte duita order dey, duitai pore "balance 40", duitai 40 kate. Balance hoye jay -40. `with_for_update()` PostgreSQL e oi customer er row te **tala** dey: ditiyo request ta prothom ta shesh na howa porjonto opekkha kore. SQLite e tala lage na, karon she ek shomoy ekjon kei likhte dey. Race condition er choturtho rup (Lesson 3, 6, 7, 8), ebar shomadhan "tala".

Order `cancelled` ba `rejected` hole khoroch kora credit `+` line hoye fire ashe. Test: `test_cancelling_gives_spent_credit_back`.

## 6. Demo te 40 minute boshe thakbe?

Na. Er jonno ekta helper script:

```bash
python -m scripts.make_order_late 1 20
```

Eta 1 number order er `promised_at` ke otit e shoriye dey, jate ekhon deliver korle "20 minute late" gona hoy. Shudhu demo r jonno, ashol customer er data te kokhono na.

## 7. Swagger e try koro

1. Lesson 7 er golpo ta `ready` porjonto nao (rider claim kore rekheche)
2. Terminal e: `python -m scripts.make_order_late <order_id> 20`
3. **Rider:** `picked_up`, tarpor `delivered`. Uttor e `late_minutes: 20`, `compensation: 40`
4. **Customer:** `GET /wallet`. Balance 40, karon shoho
5. **Customer:** cart e abar item, `POST /orders` e `"use_wallet": true`. `wallet_used` ar `amount_due` dekho
6. Oi order ta `cancelled` koro, abar `GET /wallet`. 3 ta line, balance abar 40

## 8. Nije koro

1. Notun dhap: **60 minute er beshi** late hole puro `total` ferot.
   Age `tests/test_compensation.py` te test lekho (60 e purono niyom, 61 e notun), fail dekho, tarpor `compensation.py` bodlao. `orders.py` te hat dite holo?
2. `GRACE_MINUTES` 15 theke 10 koro. Kon kon test fail korlo? Keno? Firiye rakho.
3. `GET /wallet` e shob shomoy shesh 50 ta line ashe. Lesson 4 er moto `limit` / `offset` jog koro.
4. Bhabo: compensation er taka ke dey? Ekhon platform. Restaurant deri korle restaurant, rider deri korle rider dile nyajyo hoto. Sheta mapte ki ki shomoy likhe rakhte hoto? (Hint: `accepted_at`, `ready_at`, `picked_up_at`.)
5. Viva proshno:
   - Ledger ki? Balance column na rekhe ki labh?
   - Rating e hishab save korechi, wallet e kori ni. Keno?
   - Double spend ki? Kivabe atkano hoy?
   - Boundary testing ki? Ei project theke udahoron dao.
