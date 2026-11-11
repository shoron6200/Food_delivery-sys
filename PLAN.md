# Food Delivery System: Master Plan (Banglish)

> Working name: **[Tomar App Name]**. Name pore fix korbe, plan ta name-independent.
> Goal: prothome **minimal backend (MVP)**, tarpor phase by phase feature add.

---

## 1. Keno manush Foodpanda/Foodi chhere AMAR app use korbe?

Shudhu "arekta food app" banale keu switch korbe na. Amader ekta **clear promise** lagbe.
Bangladesh e user der real complaint gula dhore solve korte hobe:

| User er real problem | Amader solution (USP) |
|---|---|
| App e menu price restaurant er cheye beshi, hidden charge, checkout e giye total bere jay | **"Honest Price" guarantee**: menu price = restaurant er dokaner price. Checkout er age full breakdown (food + delivery + platform fee), kono surprise na |
| ETA bole 30 min, ase 70 min e, khabar thanda | **AI Honest ETA** + **Late hole auto compensation**: promised time er 15 min er beshi late hole automatic wallet credit, complain korte hobe na |
| Item missing / wrong item, refund er jonno support e 30 min chat | **1-tap Photo Refund**: chobi tulo, AI check kore, eligible hole instant refund/credit |
| Restaurant der 25-30% commission, tai tara price baray | **Low commission / flat subscription model** restaurant er jonno, tai khabar sosta thake |
| Ki khabo decide korte 20 min scroll | **AI Food Assistant**: "300 takar moddhe jhal kichu, 2 jon" bollei 3 ta best option |
| Healthy/diet/allergy filter nai | **Health mode**: calorie estimate, allergy filter, "gym-friendly", "diabetic-friendly" tag |
| Office e group order kora jhamela, ke koto dibe hishab | **Group Order + Split Bill** (bKash/Nagad diye prottek jon nijer share pay) |
| Restaurant er kitchen kemon, hygiene jani na | **Kitchen Trust Score**: hygiene rating, verified kitchen photo, real (fake-filtered) review |
| Ghorer moto khabar pai na | **Home Chef section**: verified home cook der "ghorer khabar" + tiffin subscription (daily lunch) |
| Rider ra underpaid, rude/rush behavior | **Fair Rider Pay**: transparent per-trip earning + tip 100% rider pay. Happy rider = better service |

### Amader one-line identity
> **"No hidden charge. Late hole amra pay kori. AI bole dey ki khabe."**

Ei 3 ta jinish marketing er main point. Baki sob feature egula ke support kore.

---

## 2. User types (Roles)

1. **Customer**: khabar order kore
2. **Restaurant / Home Chef (Vendor)**: menu manage, order accept/reject
3. **Rider**: delivery kore
4. **Admin**: sob kichu control, refund approve, vendor verify

MVP te 4 ta role er **API** thakbe, kintu UI pore.

---

## 3. Tech Stack (Recommended)

| Part | Choice | Keno |
|---|---|---|
| Backend | **Python + FastAPI** | Fast, auto API docs (Swagger), AI/ML integration Python e shobcheye easy |
| Database | **SQLite** (ekhon) → **PostgreSQL** (pore) | SQLite e kichu install lage na, shekhar jonno shohoj. Pore shudhu `DATABASE_URL` bodlalei PostgreSQL |
| ORM | SQLAlchemy 2.0 (Alembic migration pore) | Standard, stable |
| Auth | JWT access token (refresh token + phone OTP pore) | Simple, mobile friendly |
| Cache / Queue (Phase 2) | Redis | Rider location, real-time order status, rate limit |
| Real-time (Phase 2) | WebSocket (FastAPI built-in) | Live order tracking |
| Payment (Phase 2) | Cash on Delivery → pore bKash / Nagad / SSLCommerz | BD market |
| AI (Phase 3) | LLM API (chat/assistant) + simple ML (ETA, recommendation) | |
| Deploy (pore) | Docker + Docker Compose → VPS / Railway / Render | Cheap start |
| Frontend (pore) | Customer: React Native / Flutter, Admin: React (Next.js) | |

---

## 4. Phase-wise Roadmap

### Phase 0: Setup (1-2 din)
- [x] Project structure, virtualenv, FastAPI hello world
- [x] SQLite database, `.env` config
- [x] Basic README
- [ ] (pore) PostgreSQL + Docker Compose + Alembic migration

### Phase 1: Minimal Backend MVP (2-3 week) ⭐ ekhane shuru
Goal: **ekta order shuru theke shesh porjonto API diye complete kora jabe.**

- [x] **Auth**: register, login, JWT, role (customer/vendor/rider/admin)
- [x] **Restaurant**: create/update (vendor), list/search (customer), open/close status
- [x] **Menu**: item create/update, category, price, available on/off
- [x] **Cart**: add/remove item (ek somoy ek restaurant)
- [x] **Order**: place order (COD), status flow, order history
- [x] **Honest Price breakdown**: `/cart` e food + delivery + fee alada kore dekhabe
- [x] **Rider**: available orders dekha, claim, status update (picked/delivered)
- [x] **Admin**: restaurant approve, sob order dekha
- [x] **Rating & review**: delivered order er por only (fake review kombe)
- [ ] Swagger docs e sob test kora jabe

**Order status flow:**
```
placed → accepted (restaurant) → ready (restaurant)
       → picked_up (rider) → delivered (rider)
placed → rejected (restaurant) / cancelled (customer)
```

### Phase 2: Real App er moto (3-4 week)
- [ ] Phone OTP login
- [ ] Address + location (lat/lng), distance diye delivery fee calculate
- [ ] Nearby restaurant (radius search)
- [ ] Live order tracking (WebSocket + Redis e rider location)
- [ ] Push notification (FCM)
- [ ] bKash/Nagad/SSLCommerz payment
- [ ] Wallet + credit system (refund/compensation ekhane jabe)
- [ ] **Late Compensation engine**: promised_eta vs delivered_at compare, auto credit
- [ ] Coupon/promo

### Phase 3: AI Features (ongoing) 🤖
Shohoj theke kothin order e:

1. **Smart Recommendation**: order history + time (dupur/raat) + weather diye "Tomar jonno" list
2. **AI Food Assistant (chat / Banglish)**:
   - "500 takay 3 jon er dinner, biryani na" → menu theke filter kore combo suggest
   - Bangla + Banglish + English sob bujhbe
   - Pore **voice order** ("Gotobar er order ta abar dao")
3. **AI Honest ETA**: restaurant er real prep time history + distance + traffic time slot diye ETA predict
4. **Photo Refund Check**: customer er chobi + order item compare, obvious case auto approve, baki admin e
5. **Fake Review Detection**: same device/pattern, ordered na kore review, spammy text flag
6. **Health Mode**: item description theke calorie/allergen estimate, diet filter
7. **Demand Forecast (vendor er jonno)**: "Shukrobar dupure biryani 40% beshi bikri hoy, ready thako"
8. **Smart Reorder**: "Protidin 1 tay tumi lunch order koro, ajke o same?" 1-tap

### Phase 4: Unique Growth Features
- [ ] **Group Order + Split Bill** (shareable link, sobai nijer item add kore)
- [ ] **Home Chef + Tiffin Subscription** (weekly/monthly lunch plan)
- [ ] **Kitchen Trust Score** (hygiene inspection badge)
- [ ] **Lite mode** (kom internet/low-end phone er jonno halka UI)
- [ ] Loyalty: order korle points, rider/restaurant ke rate korle points

---

## 5. Hassle-free UX Principles (frontend banano r somoy follow korbo)

1. **3 tap e order**: Home → Item → Order. Reorder 1 tap.
2. **Checkout e kono surprise na**: total price prothom thekei dekhabe.
3. **Login chhara browse** kora jabe, order er somoy OTP.
4. **Bangla/English toggle**, Banglish search bujhbe ("kacchi", "kachhi", "কাচ্চি" sob same result).
5. **Clear status**: "Restaurant ranna korche (aro ~12 min)" type er human message.
6. **Problem hole 1 button**: "Somossa?" → missing/wrong/late → instant solution, chat e ghurte hobe na.
7. **Cash on Delivery first-class**: BD te ekhono beshi manush COD use kore.

---

## 6. Database Design (MVP)

```
users            (id, name, phone, password_hash, role, is_active, created_at)
addresses        (id, user_id, label, address_text, lat, lng, is_default)
restaurants      (id, owner_id, name, description, address,
                  is_open, avg_prep_minutes, created_at)
                  -- pore: is_approved (Step 7), rating (Step 8), lat, lng (Phase 2)
menu_items       (id, restaurant_id, name, description, price, category, is_available)
                  -- price = purno taka (int). pore: image_url, tags (spicy, veg, healthy...)
cart_items       (user_id, menu_item_id, quantity)
                  -- primary key = (user_id, menu_item_id). dam rakhi na, menu theke pori
orders           (id, customer_id, restaurant_id, rider_id, address_id, status,
                  subtotal, delivery_fee, platform_fee, discount, total,
                  payment_method, payment_status,
                  promised_eta, delivered_at, created_at)
order_items      (id, order_id, menu_item_id, name_snapshot, price_snapshot, quantity)
order_status_log (id, order_id, status, changed_by, created_at)
reviews          (id, order_id, customer_id, restaurant_id, rating, comment, created_at)
```

**Note:** `order_items` e `price_snapshot` rakhchi karon pore menu price change hole purono order er hishab thik thakbe. `promised_eta` + `delivered_at` diye Phase 2 te late compensation calculate hobe.

---

## 7. API Endpoints (MVP)

```
# Auth
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/me

# Restaurants (public + vendor)
GET    /api/v1/restaurants?search=&limit=&offset=
GET    /api/v1/restaurants/{id}
GET    /api/v1/restaurants/{id}/menu
POST   /api/v1/restaurants                      (vendor)
PATCH  /api/v1/restaurants/{id}                 (vendor)
POST   /api/v1/restaurants/{id}/menu-items      (vendor, malik)
PATCH  /api/v1/menu-items/{id}                  (vendor, malik)

# Cart
GET    /api/v1/cart                          ← Honest Price breakdown shoho
PUT    /api/v1/cart/items/{menu_item_id}     (quantity set kore)
DELETE /api/v1/cart/items/{menu_item_id}
DELETE /api/v1/cart                          (cart khali)

# Orders
POST   /api/v1/orders                (customer, cart theke)
GET    /api/v1/orders                (nijer orders)
GET    /api/v1/orders/{id}
POST   /api/v1/orders/{id}/cancel
PATCH  /api/v1/vendor/orders/{id}/status    (accept/reject/preparing/ready)

# Rider
GET    /api/v1/rider/orders/available
POST   /api/v1/rider/orders/{id}/accept
PATCH  /api/v1/rider/orders/{id}/status     (picked_up/delivered)

# Review
POST   /api/v1/orders/{id}/review

# Admin
GET    /api/v1/admin/restaurants?approved=false
POST   /api/v1/admin/restaurants/{id}/approve
GET    /api/v1/admin/orders
```

---

## 8. Folder Structure

```
Food_delivery-sys/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── core/                # config, security (JWT, hashing), dependencies
│   ├── db/                  # session, base
│   ├── models/              # SQLAlchemy models (user, restaurant, order...)
│   ├── schemas/             # Pydantic request/response
│   ├── api/v1/              # routers: auth, restaurants, cart, orders, rider, admin
│   ├── services/            # business logic (pricing, order flow, eta)
│   └── ai/                  # Phase 3: recommendation, assistant, eta model
├── docs/lessons/            # step by step lesson (Banglish)
├── alembic/                 # DB migrations (pore)
├── tests/
├── docker-compose.yml       # (pore)
├── Dockerfile               # (pore)
├── requirements.txt
├── .env.example
└── README.md
```

**Rule:** router e logic na, `services/` e business logic. Tahole pore AI/feature add korle code clean thakbe.

---

## 9. Business Model (short)

- Restaurant: **low commission (~10-12%)** othoba flat monthly subscription; competitor er 25-30% er cheye kom
- Customer: choto transparent platform fee (e.g. 5-10 tk), optional **Pro subscription** (free delivery + priority + extra compensation)
- Home Chef: listing free, per-order choto fee
- Pore: vendor der jonno AI demand-forecast/analytics paid feature

---

## 10. Varsity Project Version (2nd year) + Shekhar Plan

Ei project ta mainly **varsity project**, ar banate banate shekha o uddeshyo. Tai:

**Scope:** Phase 1 (full order flow) + 2 ta unique feature (Honest Price, Late Compensation) + 1 ta AI feature. Etotukui ekta strong project. Phase 2-4 er baki ongsho report e "Future Work" hisebe jabe.

**Kaj er niyom:** protita step e 4 ta jinish thakbe:
1. Kaj kora code (chhoto, porar moto)
2. Automatic test
3. Banglish lesson (`docs/lessons/`): ki banalam, keno, line by line
4. "Nije koro" exercise

| Step | Ki banabo | Ki shikhbo | Status |
|---|---|---|---|
| 1 | Setup, prothom endpoint | HTTP, API, FastAPI, Swagger | ✅ |
| 2 | Database, `users` table | ORM, model vs schema, session | ✅ |
| 3 | Register, login, `/me` | Password hash, JWT, `Depends` | ✅ |
| 4 | Restaurant + Menu | CRUD, foreign key, relationship, role permission (403) | ✅ |
| 5 | Cart + Honest Price | Business logic, `services/` layer | ✅ |
| 6 | Order + status flow | State machine, transaction, price snapshot | ✅ |
| 7 | Rider + Admin | Role based access, admin script | ✅ |
| 8 | Review + rating | Aggregate query, validation rule | ✅ |
| 9 | Late Compensation | Datetime logic, wallet/credit | ✅ |
| 10 | AI feature (recommendation / Banglish assistant) | LLM API, prompt, external API call | |

**Varsity te joma dewar jonno (shesh er dike banabo):**
- ER diagram (database design)
- Use case diagram (4 ta role)
- API documentation (Swagger nije theke banay)
- Test report (`pytest` output)
- Live demo: ekta order shuru theke shesh
