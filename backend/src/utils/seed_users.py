"""
Utils: seed_users.py
Creates initial admin users in the database.
Run once after migration: python -m src.utils.seed_users
"""
import asyncio
from sqlalchemy import select
from src.models.base import AsyncSessionLocal
from src.models.entities import User
from src.core.security import get_password_hash

DEFAULT_USERS = [
    {"username": "admin", "email": "admin@amrnexus.org", "password": "AMRNexus2026!", "role": "National Coordinator"},
    {"username": "vet_coord", "email": "vet@amrnexus.org", "password": "AMRNexus2026!", "role": "County Veterinarian"},
    {"username": "clinician", "email": "clinic@amrnexus.org", "password": "AMRNexus2026!", "role": "County Clinician"},
]


async def seed():
    async with AsyncSessionLocal() as db:
        for u in DEFAULT_USERS:
            result = await db.execute(select(User).where(User.username == u["username"]))
            existing = result.scalar_one_or_none()
            if not existing:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    role=u["role"],
                    is_active=True,
                )
                db.add(user)
                print(f"Created user: {u['username']} ({u['role']})")
            else:
                print(f"User already exists: {u['username']}")
        await db.commit()
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
