# Lesson 10: "Tomar Jonno" Recommendation

Ei lesson er code: `app/services/recommend.py`, `app/services/catalog.py`, `app/schemas/recommendation.py`, `app/api/v1/recommendations.py`

Plan er problem ta mone koro: "ki khabo decide korte 20 minute scroll". Ei step e app nijei bole dey, **ar keno bolche shetao bole.**

Database e notun kichu ashe ni, file muchte hobe na.

## 1. Ki banalam

`GET /recommendations` (customer). Uttor er ekta line:

```json
{
  "item": {"id": 4, "name": "Tehari", "category": "Biryani", "price": 200,
           "restaurant": {"id": 2, "name": "Burger Lab", "average_rating": 4.5}},
  "score": 9.5,
  "reason": "Because you like Biryani"
}
```

## 2. Shoja kotha: eta ki "AI"?

Eta ekta **rule-based recommender**: amra niyom likhe diyechi, computer shudhu hishab kore. Machine learning (data theke nije niyom shekha) ekhane nai. Recommendation system er **shobcheye shohoj dhap** eta, ar report e etake "content-based filtering" bolbe, "deep learning" na. Bhasha bojha AI ashbe Lesson 11 e.

Ekhane ML na newar karon o ache: ML er jonno hajar hajar order er data lage. Notun app e sheta thake na.

## 3. Content-based filtering

Recommendation er duita boro poth:

| | Content-based (amader) | Collaborative |
|---|---|---|
| Buddhi | "**Tumi** age ja kheyecho, tar moto" | "**Tomar moto manush** ja kheyeche" |
| Lage | Shudhu tomar itihash + item er tothyo | Onek user er onek data |
| Notun app e | kaj kore | kaj kore na |

## 4. Score er formula

Protita item ekta **score** pay, tarpor boro theke chhoto shajano hoy:

```
score = restaurant er rating              (0-5; review na thakle 3.0)
      + 5 × category share                (0 theke 5)
      + 2, jodi age ei item order kore thako
```

**Category share** mane tomar age r khawar koto bhag ei category r. 4 ta item kheyecho, 3 ta Biryani: share = 3/4 = 0.75, tai Biryani pay `5 × 0.75 = 3.75`.

Udahoron (rating 4.5 er restaurant er Tehari, tumi 75% Biryani khao, Tehari age khao ni):

```
4.5 + 5 × 0.75 + 0 = 8.25
```

Shonkha gula (`5.0`, `2.0`, `3.0`) file er upore naam diye rakha: `CATEGORY_WEIGHT`, `REORDER_BONUS`, `NEUTRAL_RATING`. Egula ke bole **weight**. Bodlale app er shobhab bodlay. ML e ei weight gulai data theke shekha hoy; amra hate boshiyechi.

## 5. Cold start

Notun customer er kono itihash nai. Eke bole **cold start problem**. Tokhon formula r majher ar shesh ongsho 0, thake shudhu rating: bhalo rating er restaurant age.

Notun restaurant er o ek e shomossa: review nai. Take 0 dhorle she kokhono upore uthto na, review o peto na. Tai `NEUTRAL_RATING = 3.0`: "ojana mane majhari, kharap na".

## 6. `reason`: keno dekhacchi sheta bola

```python
if item.id in ordered_before:
    reason = "You ordered this before"
elif category_share > 0:
    reason = f"Because you like {item.category}"
elif rating is not None and rating >= 4:
    reason = "From a highly rated restaurant"
else:
    reason = "Something new to try"
```

Eke bole **explainability**. User jane keno eta dekhano hocche, tai bishwash kore. "Honest" app er shathe eta mile. Rule-based system er boro labh etai: protita uttor ek line e bojhano jay. ML model e eta kothin.

## 7. Code er gothon

Abar ek e bhag (Lesson 5):

| File | Kaj | Database chhoy? |
|---|---|---|
| `services/recommend.py` | score, shajano, reason | **na** (pure) |
| `services/catalog.py` | ekhon ki ki order kora jay | hya |
| `api/v1/recommendations.py` | customer er itihash ane, duita ke jora dey | hya |

Itihash anar query te **duita JOIN**:

```python
select(OrderItem.menu_item_id, MenuItem.category, OrderItem.quantity)
    .join(Order, OrderItem.order_id == Order.id)
    .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
    .where(Order.customer_id == customer.id, Order.status == OrderStatus.delivered)
```

JOIN mane foreign key dhore duita table er row pasha-pashi boshano. Ekhane `order_items` theke shuru kore `orders` (kar order, delivered kina) ar `menu_items` (kon category) e jawa hoyeche.

Shudhu **delivered** order gona hoy. Batil kora order ruchi r proman na.

Ar `get_orderable_items` shudhu emon item dey ja **ekhon order kora jay**: available, restaurant khola ar approved. Bondho dokaner khabar dekhano mane user ke hotash kora.

## 8. Swagger e try koro

1. Admin, vendor, 2 ta restaurant (alada category r item), customer, rider banao
2. **Customer:** `GET /recommendations`. Shob "Something new to try"
3. Ekta Biryani order kore `delivered` porjonto nao
4. Abar `GET /recommendations`. Upore ki elo, `reason` ki?
5. Review dao (Lesson 8), abar dekho. Score bodlalo?

## 9. Nije koro

1. `CATEGORY_WEIGHT` 5 theke 1 koro. `tests/test_recommend.py` er kon test fail kore? Test er naam ta poro: keno fail korlo bujhte parcho? Firiye rakho.
2. Notun niyom: **shomoy onujayi**. Shokal 6-11 tay category "Breakfast" hole +2.
   `recommend` e `hour: int` parameter jog koro (function er bhitore `datetime.now()` likho na, baire theke pathao). Keno baire theke? (Hint: test e shokal 8 ta kivabe banabe?)
3. `GET /recommendations` e `max_price` query parameter jog koro.
4. Viva proshno:
   - Content-based ar collaborative filtering er parthokko ki? Amra kon ta, keno?
   - Cold start problem ki? Amra kivabe shamlai?
   - Eta ki machine learning? (Shot uttor: na, rule-based. Weight hate boshano.)
   - Explainability ki, keno dorkar?
