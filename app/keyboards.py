from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import PAYMENT_LINK



share_contact_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Поділитися номером", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

def payment_link_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатити стікери", url=PAYMENT_LINK)]
        ]
    )

def confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"confirm:{user_id}"),
                InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject:{user_id}"),
            ]
        ]
    )