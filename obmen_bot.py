# obmen_bot.py — rangli tugmalar bilan to'liq versiya
# -*- coding: utf-8 -*-
import os
import json
import time
import logging
from datetime import datetime
import pytz
from typing import Any
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

API_TOKEN = os.getenv("OBMEN_BOT_TOKEN", "8298808352:AAHkD1lraFUAy8xyToDBYX0CMo4twRQ2yYE")
ADMIN_ID = int(os.getenv("OBMEN_ADMIN_ID", "8537782289"))
CHANNEL_USERNAME = "@tlovchek"
DATA_DIR = "bot_data"
CURRENCIES_FILE = os.path.join(DATA_DIR, "currencies.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
HELP_VIDEO_FILE = os.path.join(DATA_DIR, "help_video.json")
RESERVES_FILE = os.path.join(DATA_DIR, "reserves.json")
CARD_BALANCE_FILE = os.path.join(DATA_DIR, "card_balance.json")

os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

def load_json(path: str, default: Any):
    if not os.path.exists(path):
        save_json(path, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception("Faylni o'qishda xato (%s): %s", path, e)
        return default

def save_json(path: str, data: Any):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("Faylga yozishda xato (%s): %s", path, e)

currencies = load_json(CURRENCIES_FILE, {})
users = load_json(USERS_FILE, {})
orders = load_json(ORDERS_FILE, {})
help_video_data = load_json(HELP_VIDEO_FILE, {"video": None, "text": "Qo'llanma hali qo'shilmagan."})
reserves = load_json(RESERVES_FILE, {})
card_balance = load_json(CARD_BALANCE_FILE, {"UZS": 0})


class BuyFSM(StatesGroup):
    choose_currency = State()
    amount = State()
    wallet = State()
    confirm = State()
    upload = State()

class SellFSM(StatesGroup):
    choose_currency = State()
    amount = State()
    wallet = State()
    confirm = State()
    upload = State()

class AdminFSM(StatesGroup):
    main = State()
    add_choose_code = State()
    add_choose_name = State()
    add_set_buy_rate = State()
    add_set_sell_rate = State()
    add_set_buy_card = State()
    add_set_sell_card = State()
    edit_choose_currency = State()
    edit_field_choose = State()
    edit_set_value = State()
    delete_choose = State()
    reserves_choose_currency = State()
    reserves_set_amount = State()
    card_set_amount = State()
    broadcast_choose = State()
    broadcast_target = State()
    broadcast_media = State()
    help_video_set_video = State()
    help_video_set_text = State()

class ContactAdminFSM(StatesGroup):
    wait_message = State()

class AdminReplyFSM(StatesGroup):
    wait_reply = State()


def is_admin(user_id):
    try:
        return str(user_id) == str(ADMIN_ID)
    except:
        return False

def ensure_user(uid, user=None):
    key = str(uid)
    if key not in users:
        users[key] = {
            "id": int(uid),
            "name": user.full_name if user else "",
            "username": user.username if user else "",
            "joined_at": int(time.time()),
            "orders": []
        }
        save_json(USERS_FILE, users)
    return users[key]

def new_order_id():
    return str(int(time.time() * 1000))

def is_working_hours():
    tz = pytz.timezone("Asia/Tashkent")
    now = datetime.now(tz)
    return 8 <= now.hour < 22


# ============================================================
# 🎨 RANGLI TUGMALAR
# style="primary"  = 🔵 Ko'k
# style="success"  = 🟢 Yashil
# style="danger"   = 🔴 Qizil
# ============================================================

def main_menu_kb(uid=None):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # 🔵 Ko'k — kurs ko'rish
    kb.row(
        types.KeyboardButton("📉 Sotish kursi", style="primary"),
        types.KeyboardButton("📈 Sotib olish kursi", style="primary"),
    )
    # 🟢 Yashil — asosiy amallar
    kb.row(
        types.KeyboardButton("💲 Sotib olish", style="success"),
        types.KeyboardButton("💰 Sotish", style="success"),
    )
    # 🔵 Ko'k — ma'lumotlar
    kb.row(
        types.KeyboardButton("📋 Mening buyurtmalarim", style="primary"),
        types.KeyboardButton("🕒 Ish vaqti", style="primary"),
    )
    kb.row(
        types.KeyboardButton("📖 Foydalanish qo'llanmasi", style="primary"),
        types.KeyboardButton("💳 Karta va kripto zaxiralari", style="primary"),
    )
    kb.add(types.KeyboardButton("📨 Adminga xabar yuborish", style="primary"))
    # 🔴 Qizil — admin
    if uid and is_admin(uid):
        kb.add(types.KeyboardButton("⚙️ Admin Panel", style="danger"))
    return kb

def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # 🔴 Qizil
    kb.add(types.KeyboardButton("⏹️ Bekor qilish", style="danger"))
    return kb

def confirm_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # 🟢 Yashil — tasdiqlash
    kb.add(types.KeyboardButton("✅ Chek yuborish", style="success"))
    # 🔴 Qizil — bekor
    kb.add(types.KeyboardButton("⏹️ Bekor qilish", style="danger"))
    return kb

def admin_panel_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # 🔵 Ko'k
    kb.row(
        types.KeyboardButton("➕ Valyuta qo'shish", style="primary"),
        types.KeyboardButton("✏️ Valyuta tahrirlash", style="primary"),
    )
    # 🔴 Qizil + 🔵 Ko'k
    kb.row(
        types.KeyboardButton("🗑 Valyuta o'chirish", style="danger"),
        types.KeyboardButton("📊 Zaxirani o'rnatish", style="primary"),
    )
    # 🟢 Yashil
    kb.row(
        types.KeyboardButton("💳 Karta balansini o'rnatish", style="success"),
        types.KeyboardButton("📢 Xabar yuborish", style="success"),
    )
    # 🔵 Ko'k
    kb.row(
        types.KeyboardButton("🎥 Qo'llanma o'rnatish", style="primary"),
        types.KeyboardButton("📋 Buyurtmalar", style="primary"),
    )
    # 🔴 Qizil — chiqish
    kb.add(types.KeyboardButton("🔙 Asosiy menyu", style="danger"))
    return kb

def admin_order_kb(order_id: str, user_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    # 🟢 Yashil
    kb.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_order|confirm|{order_id}", style="success"))
    # 🔴 Qizil
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data=f"admin_order|reject|{order_id}", style="danger"))
    # 🔵 Ko'k
    kb.add(types.InlineKeyboardButton("✉️ Foydalanuvchiga xabar", callback_data=f"admin_order|message_user|{user_id}", style="primary"))
    return kb


# ============================================================
# HANDLERLAR
# ============================================================

def main_menu_text_filter(text: str):
    return lambda m: m.text == text

@dp.message_handler(main_menu_text_filter("📉 Sotish kursi"))
async def show_sell_rates(message: types.Message, state: FSMContext):
    await state.finish()
    if not currencies:
        return await message.answer("⚠️ Hozircha valyuta mavjud emas.")
    text = "📉 *Sotish kurslari (Siz bizga sotasiz — biz arzon sotib olamiz):*\n"
    for code, info in currencies.items():
        name = info.get("name", code)
        buy_rate = info.get("buy_rate", "—")
        try:
            formatted = f"{float(buy_rate):,}".replace(",", " ")
        except:
            formatted = str(buy_rate)
        text += f"{code} — {name}: {formatted} UZS\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=main_menu_kb())

@dp.message_handler(main_menu_text_filter("📈 Sotib olish kursi"))
async def show_buy_rates(message: types.Message, state: FSMContext):
    await state.finish()
    if not currencies:
        return await message.answer("⚠️ Hozircha valyuta mavjud emas.")
    text = "📈 *Sotib olish kurslari (Siz bizdan sotib olasiz — biz qimmat sotasiz):*\n"
    for code, info in currencies.items():
        name = info.get("name", code)
        sell_rate = info.get("sell_rate", "—")
        try:
            formatted = f"{float(sell_rate):,}".replace(",", " ")
        except:
            formatted = str(sell_rate)
        text += f"{code} — {name}: {formatted} UZS\n"
    await message.answer(text, parse_mode="Markdown", reply_markup=main_menu_kb())

@dp.message_handler(main_menu_text_filter("🕒 Ish vaqti"))
async def show_working_hours(message: types.Message, state: FSMContext):
    await state.finish()
    text = (
        "📅 *Ish vaqtimiz:*\n"
        "Dushanbadan – Yakshanbagacha\n"
        "🕗 08:00 – 🕙 22:00\n"
        "⚠️ Eslatma: Tungi soat 22:00 dan ertalab 08:00 gacha buyurtma qabul qilinmaydi."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_menu_kb())

@dp.message_handler(main_menu_text_filter("💳 Karta va kripto zaxiralari"))
async def show_reserves(message: types.Message, state: FSMContext):
    await state.finish()
    text = "📦 <b>Kripto zaxiralari:</b>\n"
    if reserves:
        for cur, amount in reserves.items():
            text += f"• {cur}: <code>{amount}</code>\n"
    else:
        text += "• Ma'lumot yo'q\n"
    card_amt = card_balance.get("UZS", 0)
    text += f"\n💳 <b>Karta balansi:</b>\n• UZS: <code>{card_amt}</code>"
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())

@dp.message_handler(main_menu_text_filter("📖 Foydalanish qo'llanmasi"))
async def show_help(message: types.Message, state: FSMContext):
    await state.finish()
    video = help_video_data.get("video")
    text = help_video_data.get("text", "Qo'llanma hali qo'shilmagan.")
    if video:
        try:
            await bot.send_video(message.chat.id, video, caption=text)
        except Exception as e:
            logger.exception("Video yuborishda xato: %s", e)
            await message.answer(text)
    else:
        await message.answer(text, reply_markup=main_menu_kb())

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    uid_str = str(message.from_user.id)
    is_new = uid_str not in users
    ensure_user(message.from_user.id, message.from_user)
    if is_new:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🎉 *Yangi obunachi qo'shildi!*\n"
                f"👤 Ism: {message.from_user.full_name}\n"
                f"🆔 ID: {message.from_user.id}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception("Adminga xabar yuborishda xato: %s", e)
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}! 👋",
        reply_markup=main_menu_kb(message.from_user.id)
    )

@dp.message_handler(main_menu_text_filter("📋 Mening buyurtmalarim"))
async def my_orders(message: types.Message, state: FSMContext):
    await state.finish()
    uid = str(message.from_user.id)
    ensure_user(message.from_user.id, message.from_user)
    user_orders = users.get(uid, {}).get("orders", [])
    if not user_orders:
        return await message.answer("📭 Sizda buyurtmalar mavjud emas.", reply_markup=main_menu_kb(uid))
    text = "🧾 *Sizning so'nggi buyurtmalaringiz:*\n"
    for oid in user_orders[-10:][::-1]:
        o = orders.get(oid)
        if not o:
            continue
        created = o["created_at"] + 5 * 3600
        date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created))
        text += (
            f"ID: `{o['id']}`\n"
            f"Turi: {o['type']}\n"
            f"Valyuta: {o['currency']}\n"
            f"Miqdor: {o['amount']}\n"
            f"Holat: {o.get('status', '—')}\n"
            f"Yaratilgan: {date_str}\n"
            f"———————————————\n"
        )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_menu_kb(uid))

@dp.message_handler(main_menu_text_filter("💲 Sotib olish"))
async def buy_start(message: types.Message, state: FSMContext):
    await state.finish()
    if not is_working_hours():
        await message.answer("🕗 Hozir ish vaqti emas.")
        return
    available = [cur for cur in currencies.keys() if reserves.get(cur, 0) > 0]
    if not available:
        await message.answer("⚠️ Zaxira yetarli emas.")
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    for cur in available:
        kb.add(types.KeyboardButton(cur, style="success"))
    kb.add(types.KeyboardButton("⏹️ Bekor qilish", style="danger"))
    await message.answer("Qaysi valyutani sotib olmoqchisiz?", reply_markup=kb)
    await BuyFSM.choose_currency.set()

@dp.message_handler(main_menu_text_filter("💰 Sotish"))
async def sell_start(message: types.Message, state: FSMContext):
    await state.finish()
    if not is_working_hours():
        return await message.answer("Hozir ish vaqti emas.")
    if not currencies:
        return await message.answer("Valyuta yo'q.")
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    for cur in currencies.keys():
        kb.add(types.KeyboardButton(cur, style="primary"))
    kb.add(types.KeyboardButton("⏹️ Bekor qilish", style="danger"))
    await message.answer("Qaysi valyutani sotmoqchisiz?", reply_markup=kb)
    await SellFSM.choose_currency.set()

@dp.message_handler(main_menu_text_filter("📨 Adminga xabar yuborish"))
async def contact_admin_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Xabaringizni yuboring (matn, rasm, video):", reply_markup=back_kb())
    await ContactAdminFSM.wait_message.set()

# ========== BUY FSM ==========
@dp.message_handler(state=BuyFSM.choose_currency)
async def buy_choose_currency(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    if message.text not in currencies:
        return await message.answer("Bunday valyuta yo'q.")
    await state.update_data(currency=message.text)
    await message.answer("Miqdorni kiriting:", reply_markup=back_kb())
    await BuyFSM.next()

@dp.message_handler(state=BuyFSM.amount)
async def buy_amount(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    try:
        amt = float(message.text.replace(",", "."))
        if amt <= 0: raise ValueError()
    except:
        return await message.answer("Iltimos, to'g'ri miqdor kiriting.")
    data = await state.get_data()
    currency = data.get("currency")
    if not currency:
        await state.finish()
        return await message.answer("Xatolik.")
    if amt > reserves.get(currency, 0):
        return await message.answer(f"Zaxira yetarli emas. Mavjud: {reserves.get(currency, 0)}")
    await state.update_data(amount=amt)
    await message.answer("Hamyon raqamingizni kiriting:", reply_markup=back_kb())
    await BuyFSM.next()

@dp.message_handler(state=BuyFSM.wallet)
async def buy_wallet(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    await state.update_data(wallet=message.text.strip())
    data = await state.get_data()
    currency = data["currency"]
    amt = data["amount"]
    info = currencies[currency]
    rate = info.get("sell_rate")
    if not rate:
        await state.finish()
        return await message.answer("Narx ma'lum emas.")
    total = round(amt * float(rate), 2)
    card = info.get("sell_card", "5614 6818 7267 2690")
    await message.answer(
        f"🔔 *To'lov tafsilotlari:*\n"
        f"💳 Karta: {card}\n"
        f"💱 Valyuta: {currency}\n"
        f"🔢 Miqdor: {amt}\n"
        f"📈 Narx: {rate}\n"
        f"💰 Jami: {total} UZS\n\n"
        f"Kartaga to'lov qilgach chek yuboring 👇",
        parse_mode="Markdown",
        reply_markup=confirm_kb()
    )
    await BuyFSM.confirm.set()

@dp.message_handler(state=BuyFSM.confirm)
async def buy_confirm(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    if message.text != "✅ Chek yuborish":
        return await message.answer("Iltimos, '✅ Chek yuborish' tugmasini bosing.")
    await message.answer("✅ Chekni yuboring:", reply_markup=back_kb())
    await BuyFSM.upload.set()

@dp.message_handler(content_types=['photo', 'document'], state=BuyFSM.upload)
async def buy_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = new_order_id()
    order = {
        "id": order_id,
        "user_id": message.from_user.id,
        "currency": data["currency"],
        "amount": data["amount"],
        "wallet": data["wallet"],
        "type": "buy",
        "status": "waiting_admin",
        "created_at": int(time.time()),
        "rate": currencies[data["currency"]]["sell_rate"],
        "photo_file_id": message.photo[-1].file_id if message.photo else None,
        "document_file_id": message.document.file_id if message.document else None,
    }
    orders[order_id] = order
    uid = str(message.from_user.id)
    users.setdefault(uid, ensure_user(message.from_user.id, message.from_user))
    users[uid].setdefault("orders", []).append(order_id)
    save_json(ORDERS_FILE, orders)
    save_json(USERS_FILE, users)
    caption = (
        f"🆕 Yangi BUY buyurtma\n"
        f"👤 {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"💱 Valyuta: {data['currency']}\n"
        f"🔢 Miqdor: {data['amount']}\n"
        f"💼 Hamyon: {data['wallet']}\n"
        f"📋 Buyurtma ID: {order_id}"
    )
    kb = admin_order_kb(order_id, message.from_user.id)
    try:
        if message.photo:
            await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=kb)
        else:
            await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=kb)
    except Exception as e:
        logger.exception("Adminga yuborishda xato: %s", e)
        await message.answer("❌ Xatolik yuz berdi.")
        await state.finish()
        return
    await message.answer("✅ Chek adminga yuborildi.", reply_markup=main_menu_kb())
    await state.finish()

# ========== SELL FSM ==========
@dp.message_handler(state=SellFSM.choose_currency)
async def sell_choose_currency(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    if message.text not in currencies:
        return await message.answer("Bunday valyuta yo'q.")
    await state.update_data(currency=message.text)
    await message.answer("Miqdorni kiriting:", reply_markup=back_kb())
    await SellFSM.next()

@dp.message_handler(state=SellFSM.amount)
async def sell_amount(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    try:
        amt = float(message.text.replace(",", "."))
        if amt <= 0: raise ValueError()
    except:
        return await message.answer("Iltimos, to'g'ri miqdor kiriting.")
    await state.update_data(amount=amt)
    await message.answer("Hamyon raqamingizni kiriting:", reply_markup=back_kb())
    await SellFSM.next()

@dp.message_handler(state=SellFSM.wallet)
async def sell_wallet(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    await state.update_data(wallet=message.text.strip())
    data = await state.get_data()
    currency = data["currency"]
    amt = data["amount"]
    info = currencies[currency]
    rate = info.get("buy_rate")
    if not rate:
        await state.finish()
        return await message.answer("Narx ma'lum emas.")
    total = round(amt * float(rate), 2)
    card = info.get("buy_card", "5614 6818 7267 2690")
    await message.answer(
        f"🔔 *To'lov tafsilotlari:*\n"
        f"💳 Karta: {card}\n"
        f"💱 Valyuta: {currency}\n"
        f"🔢 Miqdor: {amt}\n"
        f"📉 Narx: {rate}\n"
        f"💰 Jami: {total} UZS\n\n"
        f"Kartaga to'lov qilgach chek yuboring 👇",
        parse_mode="Markdown",
        reply_markup=confirm_kb()
    )
    await SellFSM.confirm.set()

@dp.message_handler(state=SellFSM.confirm)
async def sell_confirm(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    if message.text != "✅ Chek yuborish":
        return await message.answer("Iltimos, '✅ Chek yuborish' tugmasini bosing.")
    await message.answer("✅ Chekni yuboring:", reply_markup=back_kb())
    await SellFSM.upload.set()

@dp.message_handler(content_types=['photo', 'document'], state=SellFSM.upload)
async def sell_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = new_order_id()
    order = {
        "id": order_id,
        "user_id": message.from_user.id,
        "currency": data["currency"],
        "amount": data["amount"],
        "wallet": data["wallet"],
        "type": "sell",
        "status": "waiting_admin",
        "created_at": int(time.time()),
        "rate": currencies[data["currency"]]["buy_rate"],
        "photo_file_id": message.photo[-1].file_id if message.photo else None,
        "document_file_id": message.document.file_id if message.document else None,
    }
    orders[order_id] = order
    uid = str(message.from_user.id)
    users.setdefault(uid, ensure_user(message.from_user.id, message.from_user))
    users[uid].setdefault("orders", []).append(order_id)
    save_json(ORDERS_FILE, orders)
    save_json(USERS_FILE, users)
    caption = (
        f"🆕 Yangi SELL buyurtma\n"
        f"👤 {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"💱 Valyuta: {data['currency']}\n"
        f"🔢 Miqdor: {data['amount']}\n"
        f"💼 Hamyon: {data['wallet']}\n"
        f"📋 Buyurtma ID: {order_id}"
    )
    kb = admin_order_kb(order_id, message.from_user.id)
    try:
        if message.photo:
            await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=kb)
        else:
            await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=kb)
    except Exception as e:
        logger.exception("Adminga yuborishda xato: %s", e)
        await message.answer("❌ Xatolik yuz berdi.")
        await state.finish()
        return
    await message.answer("✅ Chek adminga yuborildi.", reply_markup=main_menu_kb())
    await state.finish()

# ========== ADMIN PANEL ==========
@dp.message_handler(main_menu_text_filter("⚙️ Admin Panel"))
async def admin_panel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.finish()
    await message.answer("⚙️ Admin panel:", reply_markup=admin_panel_kb())
    await AdminFSM.main.set()

@dp.message_handler(lambda m: m.text == "🔙 Asosiy menyu", state="*")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb(message.from_user.id))

# ========== ADMIN ORDER CALLBACK ==========
@dp.callback_query_handler(lambda c: c.data.startswith("admin_order"))
async def admin_order_callback(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("|")
    if len(parts) < 3:
        return await call.answer("Xato.")
    action = parts[1]
    if action == "message_user":
        user_id = int(parts[2])
        await state.update_data(reply_user_id=user_id)
        await call.message.answer("Javobingizni yuboring:", reply_markup=back_kb())
        await AdminReplyFSM.wait_reply.set()
        return await call.answer()
    order_id = parts[2]
    order = orders.get(order_id)
    if not order:
        return await call.answer("Buyurtma topilmadi.")
    uid = order["user_id"]
    if action == "confirm":
        order["status"] = "✅ Tasdiqlandi"
        save_json(ORDERS_FILE, orders)
        if order["type"] == "buy":
            cur = order["currency"]
            amt = order["amount"]
            reserves[cur] = reserves.get(cur, 0) - amt
            if reserves[cur] < 0:
                reserves[cur] = 0
            save_json(RESERVES_FILE, reserves)
        try:
            await bot.send_message(uid, f"✅ Buyurtmangiz tasdiqlandi.\n🆔 ID: {order_id}")
        except:
            pass
        await call.answer("✅ Tasdiqlandi.")
    elif action == "reject":
        order["status"] = "❌ Bekor qilindi"
        save_json(ORDERS_FILE, orders)
        try:
            await bot.send_message(uid, f"❌ Buyurtmangiz bekor qilindi.\n🆔 ID: {order_id}")
        except:
            pass
        await call.answer("❌ Bekor qilindi.")

# ========== CONTACT ADMIN ==========
@dp.message_handler(content_types=types.ContentTypes.ANY, state=ContactAdminFSM.wait_message)
async def contact_admin_send(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
    caption = f"📨 *Foydalanuvchidan xabar:*\n👤 {message.from_user.full_name}\n🆔 {message.from_user.id}"
    user_text = message.caption or message.text or ""
    if user_text:
        caption += f"\n💬 {user_text}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✉️ Javob berish", callback_data=f"reply_to_user|{message.from_user.id}", style="primary"))
    try:
        if message.photo:
            await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="Markdown", reply_markup=kb)
        elif message.video:
            await bot.send_video(ADMIN_ID, message.video.file_id, caption=caption, parse_mode="Markdown", reply_markup=kb)
        elif message.document:
            await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, parse_mode="Markdown", reply_markup=kb)
        else:
            await bot.send_message(ADMIN_ID, caption, parse_mode="Markdown", reply_markup=kb)
    except Exception as e:
        logger.exception("Adminga xabar yuborishda xato: %s", e)
        await message.answer("❌ Xabar yuborib bo'lmadi.")
    await state.finish()
    await message.answer("✅ Xabaringiz adminga yuborildi.", reply_markup=main_menu_kb())

@dp.callback_query_handler(lambda c: c.data.startswith("reply_to_user"))
async def admin_reply_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Siz admin emassiz.")
    user_id = int(call.data.split("|")[1])
    await state.update_data(reply_user_id=user_id)
    await call.message.answer("Javobingizni yuboring:", reply_markup=back_kb())
    await AdminReplyFSM.wait_reply.set()

@dp.message_handler(content_types=types.ContentTypes.ANY, state=AdminReplyFSM.wait_reply)
async def admin_reply_send(message: types.Message, state: FSMContext):
    if message.text == "⏹️ Bekor qilish":
        await state.finish()
        return await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(message.from_user.id))
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    if not user_id:
        await state.finish()
        return await message.answer("Xatolik.")
    try:
        if message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
        elif message.video:
            await bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
        elif message.document:
            await bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
        else:
            await bot.send_message(user_id, message.text)
        await message.answer("✅ Xabar yuborildi.", reply_markup=main_menu_kb(message.from_user.id))
    except Exception as e:
        logger.exception("Foydalanuvchiga xabar yuborishda xato: %s", e)
        await message.answer("❌ Xabar yuborib bo'lmadi.")
    await state.finish()

@dp.message_handler()
async def unknown(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❓ Noma'lum buyruq.", reply_markup=main_menu_kb(message.from_user.id))

if __name__ == "__main__":
    print("🤖 Obmen bot ishga tushmoqda...")
    executor.start_polling(dp, skip_updates=True)
