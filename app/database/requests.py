from app.database.models import async_session
from app.database.models import User, PaymentRequest
from sqlalchemy import select, func


async  def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()


async def get_user(tg_id: int):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def update_user_data(tg_id: int, name: str, number: str, email: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            user.name = name
            user.number = number
            user.email = email
            await session.commit()


async def add_payment_request(tg_id: int, screen_file_id: str) -> int:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            raise ValueError("Користувача не знайдено")

        payment = PaymentRequest(user_id=user.id, screen=screen_file_id)
        session.add(payment)
        await session.flush()

        # Считаем номер в очереди
        count = await session.scalar(
            select(func.count(PaymentRequest.id)).where(PaymentRequest.id <= payment.id)
        )

        await session.commit()
        return count


async def confirm_latest_payment_by_tg_id(tg_id: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return False

        payment = await session.scalar(
            select(PaymentRequest)
            .where(PaymentRequest.user_id == user.id)
            .order_by(PaymentRequest.id.desc())
        )
        if not payment:
            return False

        payment.confirmed = True
        await session.commit()
        return True