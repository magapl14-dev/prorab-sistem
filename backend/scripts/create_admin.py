"""
Create first admin user.
Usage: python -m scripts.create_admin
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
    phone = input("Телефон администратора (+7...): ").strip()
    name = input("Имя: ").strip()
    pin = input("PIN (4 цифры): ").strip()

    if len(pin) != 4 or not pin.isdigit():
        print("PIN должен быть 4 цифры")
        return

    phone = normalize_phone(phone)

    async with AsyncSessionLocal() as db:
        existing = (await db.execute(
            select(User).where(User.phone == phone, User.deleted_at.is_(None))
        )).scalar_one_or_none()

        if existing:
            print(f"Пользователь с телефоном {phone} уже существует (роль: {existing.role})")
            return

        user = User(phone=phone, name=name, pin_hash=hash_pin(pin), role="admin")
        db.add(user)
        await db.commit()
        print(f"✓ Администратор создан: {name} ({phone}), ID: {user.id}")


if __name__ == "__main__":
    asyncio.run(main())
