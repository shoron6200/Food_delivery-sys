"""Create an admin account.

Run from the project folder:  python -m scripts.create_admin

Admins cannot be made through the API on purpose (see lesson 3), so the first
one is created here, by someone who has access to the server itself.
"""

import sys
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.database import Base, SessionLocal, engine
from app.models import User, UserRole
from app.schemas.user import UserCreate


def main() -> int:
    name = input("Name: ")
    phone = input("Phone (01XXXXXXXXX): ")
    password = getpass("Password (at least 8 characters, hidden while typing): ")

    try:
        # Reuse the same rules as normal registration.
        data = UserCreate(name=name, phone=phone, password=password)
    except ValidationError as error:
        for problem in error.errors():
            print(f"Problem with {problem['loc'][0]}: {problem['msg']}")
        return 1

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.add(
            User(
                name=data.name,
                phone=data.phone,
                password_hash=hash_password(data.password),
                role=UserRole.admin,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            print("This phone number is already registered.")
            return 1

    print(f"Admin created. Log in with phone {data.phone}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
