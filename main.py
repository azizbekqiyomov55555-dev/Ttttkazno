import random
import sqlite3
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID topilmadi!")

ADMIN_ID = int(ADMIN_ID)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================= DATABASE =================
conn = sqlite3.connect("casino.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 1000,
    last_bonus INTEGER DEFAULT 0,
    referred_by INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS promocodes (
    code TEXT PRIMARY KEY,
    reward INTEGER
)
""")

conn.commit()
cursor.execute("INSERT OR IGNORE INTO promocodes VALUES ('BONUS100', 100)")
conn.commit()

# ================= MENU =================
def main_menu(user_id):
    keyboard = [
        [KeyboardButton("🎮 O‘yinlar")],
        [KeyboardButton("🎁 Bonus"), KeyboardButton("🎟 Promo kod")],
        [KeyboardButton("👤 Profil")],
        [KeyboardButton("💸 Pul chiqarish")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton("👑 Admin Panel")])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

games_list = ["🎲 Dice", "🪙 Coin Flip", "🎰 Slot"]

awaiting_bet = set()
awaiting_promo = set()
withdraw_step = {}

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                   (message.from_user.id,))
    conn.commit()

    await message.answer("🎰 Casino Botga xush kelibsiz!", 
                         reply_markup=main_menu(message.from_user.id))

# ================= PROFIL =================
@dp.message_handler(lambda m: m.text == "👤 Profil")
async def profile(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?",
                   (message.from_user.id,))
    row = cursor.fetchone()

    if row:
        await message.answer(f"💰 Balans: {row[0]}")

# ================= BONUS =================
@dp.message_handler(lambda m: m.text == "🎁 Bonus")
async def bonus(message: types.Message):
    cursor.execute("SELECT last_bonus FROM users WHERE user_id=?",
                   (message.from_user.id,))
    row = cursor.fetchone()

    if not row:
        return

    last = row[0]
    now = int(time.time())

    if now - last < 86400:
        await message.answer("⏳ 24 soatda 1 marta bonus!")
        return

    cursor.execute("UPDATE users SET balance=balance+100, last_bonus=? WHERE user_id=?",
                   (now, message.from_user.id))
    conn.commit()

    await message.answer("🎁 +100 coin qo‘shildi!")

# ================= PROMO =================
@dp.message_handler(lambda m: m.text == "🎟 Promo kod")
async def promo_start(message: types.Message):
    awaiting_promo.add(message.from_user.id)
    await message.answer("Promo kodni kiriting:")

# ================= O‘YINLAR =================
@dp.message_handler(lambda m: m.text == "🎮 O‘yinlar")
async def games(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for g in games_list:
        kb.add(KeyboardButton(g))
    kb.add(KeyboardButton("🔙 Orqaga"))
    await message.answer("O‘yinni tanlang:", reply_markup=kb)

@dp.message_handler(lambda m: m.text in games_list)
async def game_start(message: types.Message):
    awaiting_bet.add(message.from_user.id)
    await message.answer("💵 Stavka kiriting (min 10):")

# ================= PUL CHIQARISH =================
@dp.message_handler(lambda m: m.text == "💸 Pul chiqarish")
async def withdraw_start(message: types.Message):
    withdraw_step[message.from_user.id] = "amount"
    await message.answer("Qancha pul chiqarmoqchisiz?")

# ================= ADMIN PANEL =================
@dp.message_handler(lambda m: m.text == "👑 Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(balance) FROM users")
    total = cursor.fetchone()[0]

    await message.answer(
        f"📊 Statistika:\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"💰 Umumiy balans: {total}"
    )

# ================= UNIVERSAL =================
@dp.message_handler()
async def universal(message: types.Message):
    uid = message.from_user.id
    text = message.text

    # PROMO
    if uid in awaiting_promo:
        awaiting_promo.remove(uid)
        cursor.execute("SELECT reward FROM promocodes WHERE code=?", (text.upper(),))
        row = cursor.fetchone()
        if row:
            reward = row[0]
            cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                           (reward, uid))
            conn.commit()
            await message.answer(f"🎁 {reward} coin qo‘shildi!")
        else:
            await message.answer("❌ Promo kod xato")
        return

    # BET
    if uid in awaiting_bet and text.isdigit():
        awaiting_bet.remove(uid)
        bet = int(text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bet < 10 or bet > bal:
            await message.answer("❌ Stavka xato")
            return

        win = random.random() < 0.3

        if win:
            cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                           (bet, uid))
            result = f"🎉 YUTDINGIZ! +{bet}"
        else:
            cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                           (bet, uid))
            result = f"😢 YUTQAZDINGIZ! -{bet}"

        conn.commit()
        await message.answer(result)
        return

    # WITHDRAW
    if uid in withdraw_step:

        if withdraw_step[uid] == "amount" and text.isdigit():
            amount = int(text)

            cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
            bal = cursor.fetchone()[0]

            if amount < 100 or amount > bal:
                await message.answer("❌ Minimal 100 coin yoki balans yetarli emas")
                return

            withdraw_step[uid] = amount
            await message.answer("Karta raqamingizni kiriting:")
            return

        if isinstance(withdraw_step[uid], int):
            amount = withdraw_step[uid]
            card = text

            cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                           (amount, uid))
            conn.commit()

            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ok_{uid}_{amount}"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data=f"no_{uid}_{amount}")
            )

            await bot.send_message(
                ADMIN_ID,
                f"💸 Yangi pul chiqarish!\nUser: {uid}\nSumma: {amount}\nKarta: {card}",
                reply_markup=kb
            )

            await message.answer("⏳ So‘rovingiz yuborildi!")
            del withdraw_step[uid]
            return

# ================= CALLBACK =================
@dp.callback_query_handler(lambda c: c.data.startswith(("ok_", "no_")))
async def process_withdraw(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    action, user_id, amount = callback.data.split("_")
    user_id = int(user_id)
    amount = int(amount)

    if action == "ok":
        await bot.send_message(user_id, "✅ Pul chiqarish tasdiqlandi!")
        await callback.message.edit_text("✅ Tasdiqlandi")
    else:
        cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                       (amount, user_id))
        conn.commit()
        await bot.send_message(user_id, "❌ Pul chiqarish bekor qilindi")
        await callback.message.edit_text("❌ Bekor qilindi")

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
