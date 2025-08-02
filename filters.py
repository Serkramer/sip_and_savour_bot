from aiogram.filters import BaseFilter
from aiogram.types import Message
from app.database.requests import get_user

class IsRegistered(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await get_user(message.from_user.id)
        return bool(user and user.name and user.number and user.email)