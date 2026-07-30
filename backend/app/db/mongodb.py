from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.DATABASE_NAME]
        # Create indexes (idempotent)
        await self.db.users.create_index("email", unique=True)

    async def close(self):
        if self.client:
            self.client.close()

mongodb = MongoDB()