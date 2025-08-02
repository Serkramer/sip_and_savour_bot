import re
from aiogram.enums import ParseMode
from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile, CallbackQuery, ReplyKeyboardRemove
import app.keyboards as kb
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from filters import IsRegistered
import app.database.requests  as rq
from config import UK_PHONE_PATTERN, EMAIL_PATTERN, ADMINS

router = Router()


class Reg(StatesGroup):
    name = State()
    number = State()
    email = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    from_user = message.from_user
    tg_id = from_user.id

    await rq.set_user(tg_id)

    # Получаем пользователя из БД
    user = await rq.get_user(tg_id)

    # Если у пользователя не хватает данных — запускаем регистрацию
    if not user.name or not user.number or not user.email:
        await state.set_state(Reg.name)
        await message.answer_photo(
            FSInputFile("static/img/start.jpg"),
            caption="Вас вітає кав’ярня Sip & Savour.\nЩоб придбати стікери, спочатку потрібно зареєструватися. Введіть Ваше ім’я:"
        )
        return

    # Если регистрация завершена
    await message.answer_photo(
        FSInputFile("static/img/start.jpg"),
        caption="Вас вітає кав’ярня Sip & Savour.\nПосилання для оплати стікерів розташовано на кнопці нижче.\nПісля оплати ОБОВ'ЯЗКОВО скиньте скріншот з оплатою у цей чат",
        reply_markup=kb.payment_link_kb()

    )


@router.message(Reg.name)
async def cmd_reg_two(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Reg.number)
    await message.answer(
        "Поділіться своїм номером телефону:",
        reply_markup=kb.share_contact_kb
    )


@router.message(Reg.number, F.contact)
async def cmd_reg_three_contact(message: Message, state: FSMContext):
    if not message.contact or not message.contact.phone_number:
        await message.answer("Будь ласка, натисніть кнопку, щоб поділитися номером.")
        return

    await state.update_data(number=message.contact.phone_number)
    await state.set_state(Reg.email)
    await message.answer("Введіть вашу електронну пошту:", reply_markup=ReplyKeyboardRemove())


@router.message(Reg.number)
async def cmd_reg_three_text(message: Message, state: FSMContext):
    phone = message.text.strip()

    if not re.match(UK_PHONE_PATTERN, phone):
        await message.answer("Будь ласка, введіть коректний номер у форматі +380XXXXXXXXX.")
        return

    await state.update_data(number=phone)
    await state.set_state(Reg.email)
    await message.answer("Введіть вашу електронну пошту:")


@router.message(Reg.email)
async def cmd_reg_four(message: Message, state: FSMContext):
    email = message.text.strip()

    if not re.match(EMAIL_PATTERN, email):
        await message.answer("Будь ласка, введіть коректну електронну пошту.")
        return

    await state.update_data(email=email)
    data = await state.get_data()

    await rq.update_user_data(
        tg_id=message.from_user.id,
        name=data['name'],
        number=data['number'],
        email=data['email']
    )

    await message.answer("Дякуємо, реєстрація завершена!",  reply_markup=kb.payment_link_kb())

    await state.clear()



@router.message(IsRegistered(), F.photo)
async def handle_screenshot(message: Message, bot: Bot):
    tg_id = message.from_user.id
    photo_file_id = message.photo[-1].file_id

    try:
        # Получаем номер в очереди и пользователя
        queue_number = await rq.add_payment_request(tg_id, photo_file_id)
        user = await rq.get_user(tg_id)

        await message.answer(
            f"Дякуємо! Ваш номер у черзі: {queue_number}. Ми перевіримо оплату і повідомимо вас."
        )

        # Уведомляем администраторов
        for admin_id in ADMINS:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo_file_id,
                caption=(
                    f"<b>Нове підтвердження оплати</b>\n\n"
                    f"<b>Користувач:</b>\n"
                    f"👤 Ім’я: {user.name or '—'}\n"
                    f"📞 Телефон: {user.number or '—'}\n"
                    f"✉️ Email: {user.email or '—'}\n"
                    f"🆔 Telegram ID: <code>{tg_id}</code>\n"
                    f"🔢 Номер у черзі: <b>{queue_number}</b>\n\n"
                    f"👉 Для підтвердження або відхилення — скористайтесь кнопками нижче."

                ),
                parse_mode=ParseMode.HTML,
                reply_markup=kb.confirm_keyboard(tg_id)
            )

    except Exception as e:
        await message.answer(
            "Сталася помилка при збереженні. Спробуйте ще раз або зверніться до адміністратора."
        )
        print(f"[ERROR] handle_screenshot: {e}")



@router.callback_query(F.data.startswith("confirm:"))
async def handle_confirm_payment(callback: CallbackQuery):
    admin_id = callback.from_user.id
    if admin_id not in ADMINS:
        await callback.answer("У вас немає прав для підтвердження", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])
    confirmed = await rq.confirm_latest_payment_by_tg_id(user_id)

    if confirmed:
        # Отправляем пользователю подтверждение
        await callback.bot.send_message(
            chat_id=user_id,
            text="Ура! Ви успішно придбали стікери 🎉\n"
                 "Його можна забрати за адресою:\n<b>вул. Лазаряна, 10, Дніпро</b>.",
            parse_mode="HTML"
        )

        # Берём оригинальный caption и добавляем к нему статус
        original_caption = callback.message.caption or ""
        updated_caption = f"{original_caption}\n\n✅ <b>Оплата підтверджена</b>"

        await callback.message.edit_caption(
            caption=updated_caption,
            parse_mode=ParseMode.HTML,
            reply_markup=None
        )
        await callback.answer("Підтверджено ✅")
    else:
        await callback.answer("Не вдалося підтвердити ❌", show_alert=True)



@router.callback_query(F.data.startswith("reject:"))
async def handle_reject_payment(callback: CallbackQuery):
    admin_id = callback.from_user.id
    if admin_id not in ADMINS:
        await callback.answer("У вас немає прав для відхилення", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])

    # Отправка пользователю сообщения об отклонении
    await callback.bot.send_message(
        chat_id=user_id,
        text="Вашу оплату не вдалося підтвердити.\nЯкщо це помилка — зверніться до адміністратора."
    )

    original_caption = callback.message.caption or ""
    updated_caption = f"{original_caption}\n\n❌ <b>Оплата відхилена</b>"

    try:
        await callback.message.edit_caption(
            caption=updated_caption,
            parse_mode=ParseMode.HTML,
            reply_markup=None  # Убираем кнопки
        )
        await callback.answer("Відхилено ❌")
    except Exception as e:
        print(f"[ERROR] edit_caption: {e}")
        await callback.answer("Помилка при оновленні повідомлення", show_alert=True)




@router.message(Command("pay"))
async def send_payment_button(message: Message):
    await message.answer(
        "Натисніть кнопку нижче, щоб оплатити стікери 👇 \nПісля оплати ОБОВ'ЯЗКОВО скиньте скріншот з оплатою у цей чат",
        reply_markup=kb.payment_link_kb()
    )


@router.message(IsRegistered())
async def registered_but_not_photo(message: Message):
    await message.answer("Будь ласка, надішліть тільки скріншот оплати 📷.")


@router.message()
async def not_registered_handler(message: Message):
    await message.answer("Щоб продовжити, спочатку зареєструйтеся: /start")


