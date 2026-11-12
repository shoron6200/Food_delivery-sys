# Lesson 8: Review ar Rating

Ei lesson er code: `app/models/review.py`, `app/schemas/review.py`, `app/api/v1/reviews.py`, `app/models/restaurant.py` (`average_rating`)

Ei step e table e notun column jog hoyechilo. Tumi shesh obosthar code chalale database e shob age thekei ache, kichu muchte hobe na.

## 1. Ki banalam

| Endpoint | Kaj | Ke |
|---|---|---|
| `POST /orders/{id}/review` | 1-5 star + comment | oi order er customer |
| `GET /restaurants/{id}/reviews` | Review gula, notun age | shobai |

Ar protita restaurant er uttor e ekhon `average_rating` (jemon `4.3`) ar `review_count` ashe.

## 2. Verified review: fake review atkano

Onek app e je keu review dite pare, tai malik nijei 50 ta 5-star likhe rakhe. Amader 3 ta niyom:

| Niyom | Code e | Na manle |
|---|---|---|
| Order ta tomar hote hobe | `order.customer_id != customer.id` | `404` |
| Order **delivered** hote hobe | `order.status != OrderStatus.delivered` | `409` |
| Ek order e ek review | `order_id` column e `unique=True` | `409` |

Mane: **taka diye kheyecho, tobei bolte parbe, ar ek bar i.** 50 ta fake review dite hole 50 bar ashol order kore khete hobe.

Tin number niyom ta database nije atkay (`unique=True`), amra shudhu `IntegrityError` dhore `409` dei. Lesson 3 er duplicate phone er moto: "age check, tarpor save" na, **database er rule**.

## 3. Aggregate: onek row theke ekta shonkha

"Ei restaurant er gor rating koto?" er uttor ekta row te nai, **onek row mile** ber korte hoy. SQL e er jonno **aggregate function** ache:

| Function | Kaj |
|---|---|
| `COUNT(*)` | Koyta row |
| `AVG(rating)` | Gor |
| `SUM(rating)` | Jogfol |
| `MAX` / `MIN` | Shobcheye boro / chhoto |

```sql
SELECT restaurant_id, COUNT(*), AVG(rating)
FROM reviews
GROUP BY restaurant_id;
```

`GROUP BY restaurant_id` mane: "protita restaurant er row gula alada dol koro, tarpor protita dol er count ar gor dao."

## 4. Tahole amra gor ta save kore rakhi keno?

Upore r query protibar chalano jeto. Kintu `GET /restaurants` e 20 ta restaurant dekhate 20 ta restaurant er shob review gunte hoto, protibar. Review lakh chharale eta dhir.

Tai amra restaurant er row tei duita **cholti hishab** rakhi:

```python
rating_sum: Mapped[int] = mapped_column(default=0)     # shob star er jogfol
review_count: Mapped[int] = mapped_column(default=0)   # koyta review
```

Gor = `rating_sum / review_count`, jeta `average_rating` property te hoy. Pora khub druto, karon gonar kichu nai.

| | Protibar `AVG` query | Cholti hishab rakha |
|---|---|---|
| Pora | dhir (shob review gone) | druto |
| Lekha | shohoj | ektu beshi kaj (review + hishab duitai) |
| Jhuki | nai, shob shomoy thik | duita jaygay ek e tothyo, na milar bhoy |

Ek tothyo dui jaygay rakha ke bole **denormalization**. "Na milar bhoy" ta amra transaction diye atkai: review save ar hishab bodlano **ek `commit` e** (Lesson 6, section 4). Hoy duitai hobe, na hoy ektao na.

Gor (`4.33...`) na rekhe **jogfol ar shonkha** (duitai `int`) rakhar karon: notun review ele shudhu jog korlei hoy, ar `float` er gormil jome na (Lesson 4, section 4).

## 5. `column = column + 1`: database ke diye jog korano

Bhul upay:

```python
restaurant.review_count = restaurant.review_count + 1   # Python e pore, Python e jog
```

Duita review ek shathe ele duijon i pore "10", duijon i lekhe "11". Ekta review hariye gelo.

Thik upay (amader code):

```python
update(Restaurant)
    .where(Restaurant.id == order.restaurant_id)
    .values(
        rating_sum=Restaurant.rating_sum + data.rating,
        review_count=Restaurant.review_count + 1,
    )
```

Eta SQL e hoy `UPDATE restaurants SET review_count = review_count + 1 ...`. **Database nije** jog kore, ek dhape, tai duitai gona hoy. Lesson 6 ar 7 er race condition er arek rup, ebar shomadhan "database ke hishab korte dao".

## 6. Gopon tothyo: shudhu prothom naam

Review public, tai `ReviewOut` e customer er puro naam ba phone nai:

```python
@property
def customer_name(self) -> str:
    return self.customer.name.split()[0]    # "Rahim Uddin" -> "Rahim"
```

## 7. Swagger e try koro

Lesson 7, section 7 er golpo ta diye ekta order `delivered` porjonto nao. Tarpor:

1. **Customer:** `POST /orders/{id}/review` e `{"rating": 4, "comment": "Bhalo"}`
2. Ek e request abar. `409`
3. Logout kore `GET /restaurants/{id}/reviews`, tarpor `GET /restaurants/{id}`. `average_rating` dekho
4. Arekta order koro, `placed` obosthatei review dite cheshta koro. `409`

## 8. Nije koro

1. Cholti hishab thik ache kina nije milao. Koyekta review dewar por:
   ```bash
   python -c "import sqlite3; db = sqlite3.connect('food_delivery.db'); print(db.execute('SELECT restaurant_id, COUNT(*), AVG(rating) FROM reviews GROUP BY restaurant_id').fetchall()); print(db.execute('SELECT id, review_count, rating_sum FROM restaurants').fetchall())"
   ```
   Duita line er shonkha mile?
2. `GET /restaurants` e `min_rating: float | None` query parameter jog koro: gor rating er cheye kom hole baad.
   Hint: `Restaurant.rating_sum >= min_rating * Restaurant.review_count`. Bhag na kore gun keno? (Review 0 hole ki hoto?)
3. `GET /restaurants/{id}/reviews` e `rating` diye filter jog koro (shudhu 1-star gula dekhte).
4. Viva proshno:
   - Aggregate function ki? 3 ta naam bolo.
   - Denormalization ki? Ekhane keno korechi, jhuki ki, kivabe shamlai?
   - `review_count + 1` Python e na kore SQL e keno?
   - Fake review amra kivabe atkai?
