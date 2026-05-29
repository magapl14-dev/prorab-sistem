"""
Reset PIN for a user by phone.
Usage:
  python -m scripts.reset_pin <phone> <new_pin>
Example:
  python -m scripts.reset_pin +79898878181 1234
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import AsyncSessionLocal
from app.core.security import hash_pin, normalize_phone
from app.models.models import User
from sqlalchemy import select


async def main():
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.reset_pin <phone> <new_pin>")
        sys.exit(1)
    phone_raw, pin = sys.argv[1], sys.argv[2]
    if len(pin) != 4 or not pin.isdigit():
        print("PIN must be 4 digits")
        sys.exit(1)
    phone = normalize_phone(phone_raw)
    async with AsyncSessionLocal() as db:
        user = (await db.execute(
            select(User).where(User.phone == phone, User.deleted_at.is_(None))
        )).scalar_one_or_none()
        if not user:
            print(f"User with phone {phone} not found")
            sys.exit(1)
        user.pin_hash = hash_pin(pin)
        user.failed_attempts = 0
        user.locked_until = None
        await db.commit()
        print(f"OK: PIN reset for {user.name} ({phone}), role={user.role}")


if __name__ == "__main__":
    asyncio.run(main())
