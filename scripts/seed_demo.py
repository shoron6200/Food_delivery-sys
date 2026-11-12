"""DEMO HELPER: fill an empty database with accounts, restaurants and menus.

Run from the project folder:  python -m scripts.seed_demo

Creates one account for each role (all with the same password) and three
approved restaurants, so a demo can start with ordering straight away. It
refuses to run if the database already has users. The password is public
(it is printed below and lives in this file), so never use this on a real
server.
"""

import sys

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.database import Base, SessionLocal, engine
from app.models import MenuItem, Restaurant, User, UserRole

PASSWORD = "demo-pass-123"

ACCOUNTS = [
    ("Demo Admin", "01700000001", UserRole.admin),
    ("Karim Vendor", "01700000002", UserRole.vendor),
    ("Rahim Customer", "01700000003", UserRole.customer),
    ("Salam Rider", "01700000004", UserRole.rider),
]

# name, description, address, minutes to cook, [(dish, category, taka)]
RESTAURANTS = [
    (
        "Kacchi Ghor",
        "Puran Dhaka style biryani",
        "House 12, Road 5, Dhanmondi, Dhaka",
        25,
        [
            ("Kacchi Biryani", "Biryani", 320),
            ("Chicken Tehari", "Biryani", 180),
            ("Beef Rezala", "Curry", 260),
            ("Borhani", "Drinks", 60),
            ("Firni", "Dessert", 70),
        ],
    ),
    (
        "Burger Lab",
        "Fresh burgers and fries",
        "Shop 3, Gulshan Avenue, Dhaka",
        15,
        [
            ("Beef Burger", "Burger", 250),
            ("Naga Chicken Burger", "Burger", 230),
            ("French Fries", "Snacks", 110),
            ("Cold Coffee", "Drinks", 150),
        ],
    ),
    (
        "Cha Bari",
        "Tea, snacks and adda",
        "Lane 2, Mirpur 10, Dhaka",
        10,
        [
            ("Dudh Cha", "Drinks", 30),
            ("Singara (2 pcs)", "Snacks", 30),
            ("Chicken Roll", "Snacks", 90),
            ("Jhal Muri", "Snacks", 40),
        ],
    ),
]


def main() -> int:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(User)) > 0:
            print("The database already has users. Delete food_delivery.db first.")
            return 1

        password_hash = hash_password(PASSWORD)
        users = {
            role: User(name=name, phone=phone, password_hash=password_hash, role=role)
            for name, phone, role in ACCOUNTS
        }
        db.add_all(users.values())
        db.flush()  # gives the new users their ids

        for name, description, address, prep_minutes, dishes in RESTAURANTS:
            db.add(
                Restaurant(
                    owner_id=users[UserRole.vendor].id,
                    name=name,
                    description=description,
                    address=address,
                    avg_prep_minutes=prep_minutes,
                    is_approved=True,
                    menu_items=[
                        MenuItem(name=dish, category=category, price=price)
                        for dish, category, price in dishes
                    ],
                )
            )
        db.commit()

    print(f"Demo data created. Password for every account: {PASSWORD}\n")
    for name, phone, role in ACCOUNTS:
        print(f"  {role.value:<9} {phone}   {name}")
    print("\nThese accounts are for demos only. Never use this password on a real server.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
